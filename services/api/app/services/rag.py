# import asyncio
# from typing import List
# import openai
# from app.settings import settings
# from app.models.rag import SourceCitation, QueryResponse
# from app.services.retrieval import RetrievalService

# SYSTEM_PROMPT = """You are a precise, context-grounded Document Assistant.
# Answer the user's question ONLY using the facts and information provided in the Context below.
# - If the context does not contain enough information to answer, state clearly: "I cannot answer this based on the provided documents."
# - Do not make assumptions or incorporate outside information.
# - Cite your sources by appending chunk reference markers like [Chunk 1], [Chunk 2] when stating facts derived from them."""

# class RAGService:
#     def __init__(self, retrieval_service: RetrievalService):
#         self.retrieval_service = retrieval_service
#         self._openai_client = None

#     @property
#     def openai_client(self):
#         if self._openai_client is None:
#             if not settings.openai_api_key:
#                 raise ValueError("OpenAI API key is not configured in the environment.")

#             # Securely extract the OpenAI key from the SecretStr
#             api_key = settings.openai_api_key.get_secret_value()
#             self._openai_client = openai.OpenAI(api_key=api_key)

#         return self._openai_client

#     def _build_context_prompt(self, sources: List[SourceCitation]) -> str:
#         formatted_chunks = []
#         for idx, src in enumerate(sources, start=1):
#             formatted_chunks.append(
#                 f"<chunk index=\"{idx}\" id=\"{src.chunk_id}\">\n{src.text}\n</chunk>"
#             )
#         return "\n\n".join(formatted_chunks)

#     async def answer_query(self, query: str, tenant_id: str, top_k: int = 5) -> QueryResponse:
#         # 1. Retrieve tenant-isolated chunks
#         sources = await self.retrieval_service.retrieve_chunks(query, tenant_id, top_k)

#         if not sources:
#             return QueryResponse(
#                 answer="No relevant documents were found for this query in your account.",
#                 sources=[],
#                 model="gpt-4o-mini",
#             )

#         # 2. Build context and prompt
#         context_block = self._build_context_prompt(sources)
#         user_message = f"Context:\n{context_block}\n\nQuestion: {query}"

#         # 3. Call LLM using OpenAI (non-blocking)
#         def _generate():
#             return self.openai_client.chat.completions.create(
#                 model="gpt-4o-mini",
#                 temperature=0.0,
#                 messages=[
#                     {"role": "system", "content": SYSTEM_PROMPT},
#                     {"role": "user", "content": user_message}
#                 ],
#             )

#         response = await asyncio.to_thread(_generate)
#         answer_text = response.choices[0].message.content

#         return QueryResponse(
#             answer=answer_text,
#             sources=sources,
#             model="gpt-4o-mini",
#         )


import asyncio
from typing import List, cast

from app.models.rag import QueryResponse, SourceCitation
from app.services.embeddings import CohereEmbeddingClient, embedding_client
from app.services.retrieval import RetrievalService


class RAGService:
    def __init__(self, retrieval_service: RetrievalService):
        self.retrieval_service = retrieval_service
        # Safely cast for Mypy so it recognizes the .client property
        # Lazy-load the Cohere client to avoid unnecessary initialization
        self.cohere_client = cast(CohereEmbeddingClient, embedding_client).client

    def _build_context_prompt(self, sources: List[SourceCitation]) -> str:
        formatted_chunks = []
        for idx, src in enumerate(sources, start=1):
            formatted_chunks.append(f"Document [{idx}]:\n{src.text}")
        return "\n\n".join(formatted_chunks)

    async def answer_query(
        self, query: str, tenant_id: str, top_k: int = 5
    ) -> QueryResponse:
        sources = await self.retrieval_service.retrieve_chunks(query, tenant_id, top_k)

        if not sources:
            return QueryResponse(
                answer="No relevant documents were found for this query in your account.",
                sources=[],
                model="command-r-08-2024",
            )

        context_block = self._build_context_prompt(sources)

        system_prompt = (
            "You are a precise, context-grounded Document Assistant. "
            "Answer the user's question ONLY using the facts in the Context below. "
            "Cite your sources using [1], [2], etc."
        )

        user_message = f"Context:\n{context_block}\n\nQuestion: {query}"

        def _generate():
            return self.cohere_client.chat(
                model="command-r-08-2024",
                message=user_message,
                preamble=system_prompt,
                temperature=0.0,
            )

        response = await asyncio.to_thread(_generate)

        return QueryResponse(
            answer=response.text,
            sources=sources,
            model="command-r-08-2024",
        )


# If you want to use openai's GPT-4o-mini instead, you can replace the _generate method with an OpenAI API call, similar to the commented-out code above.
