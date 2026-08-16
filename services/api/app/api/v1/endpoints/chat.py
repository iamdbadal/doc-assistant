import json

from app.db.models import ChatMessage, ChatSession, get_db
from app.models.chat import ChatRequest
from app.services.llm import llm_orchestrator
from app.services.retrieval import RetrievalService
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

router = APIRouter()


async def chat_stream_generator(request: ChatRequest, db: AsyncSession):
    # 1. Session Management
    if request.session_id:
        session_id = request.session_id
    else:
        new_session = ChatSession(tenant_id=request.tenant_id, title=request.query[:50])
        db.add(new_session)
        await db.commit()
        await db.refresh(new_session)
        session_id = str(new_session.id)

    # 2. Fetch Chat History (Take the last 4 messages to save tokens)
    chat_history_text = ""
    if request.session_id:
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
        )
        result = await db.execute(stmt)
        past_messages = result.scalars().all()

        if past_messages:
            history_lines = []
            # Grab the last 4 messages (2 full turns) to prevent token overflow
            for msg in past_messages[-4:]:
                role = "User" if msg.role == "user" else "Assistant"
                history_lines.append(f"{role}: {msg.content}")

            chat_history_text = (
                "--- Previous Conversation ---\n" + "\n".join(history_lines) + "\n\n"
            )

    # 3. Persist Current User Message
    user_msg = ChatMessage(
        session_id=session_id,
        tenant_id=request.tenant_id,
        role="user",
        content=request.query,
    )
    db.add(user_msg)
    await db.commit()

    # 4. Retrieve Context via Pinecone
    retrieval_service = RetrievalService()
    sources = await retrieval_service.retrieve_chunks(
        request.query, request.tenant_id, request.top_k
    )

    formatted_chunks = [f"Document [{i+1}]:\n{s.text}" for i, s in enumerate(sources)]
    context_block = "\n\n".join(formatted_chunks)

    system_prompt = (
        "You are a precise, context-grounded Document Assistant. "
        "Answer the user's question ONLY using the facts in the Context below. "
        "Cite your sources using [1], [2], etc."
    )

    # 5. Build the final memory-injected prompt
    user_message = f"{chat_history_text}--- Current Context ---\n{context_block}\n\nQuestion: {request.query}"

    # 6. Stream response back to client (Server-Sent Events)
    full_response = ""
    try:
        meta_event = {
            "type": "meta",
            "session_id": session_id,
            "sources": [s.model_dump() for s in sources],
        }
        yield f"data: {json.dumps(meta_event)}\n\n"

        async for token in llm_orchestrator.generate_stream(
            user_message, system_prompt
        ):
            full_response += token
            token_event = {"type": "token", "content": token}
            yield f"data: {json.dumps(token_event)}\n\n"

    finally:
        # 7. Persist Assistant Message
        if full_response:
            asst_msg = ChatMessage(
                session_id=session_id,
                tenant_id=request.tenant_id,
                role="assistant",
                content=full_response,
                citations=json.dumps([s.model_dump() for s in sources]),
            )
            db.add(asst_msg)
            await db.commit()


@router.post("/stream")
async def chat_stream_endpoint(
    request: ChatRequest, db: AsyncSession = Depends(get_db)
):
    """Streaming chat endpoint using Server-Sent Events (SSE)."""
    return StreamingResponse(
        chat_stream_generator(request, db), media_type="text/event-stream"
    )
