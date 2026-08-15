from app.models.rag import QueryRequest, QueryResponse
from app.services.rag import RAGService
from app.services.retrieval import RetrievalService
from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter(prefix="/v1", tags=["Query & RAG"])


def get_rag_service() -> RAGService:
    retrieval_svc = RetrievalService()
    return RAGService(retrieval_service=retrieval_svc)


@router.post("/query", response_model=QueryResponse, status_code=status.HTTP_200_OK)
async def execute_query(
    request: QueryRequest,
    rag_service: RAGService = Depends(get_rag_service),
) -> QueryResponse:
    try:
        response = await rag_service.answer_query(
            query=request.query,
            tenant_id=request.tenant_id,
            top_k=request.top_k,
        )
        return response
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing RAG query: {str(exc)}",
        )
