from typing import List

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(..., description="The user's question")
    tenant_id: str = Field(..., description="The tenant namespace identifier")
    top_k: int = Field(
        default=5, ge=1, le=20, description="Number of context chunks to retrieve"
    )


class SourceCitation(BaseModel):
    chunk_id: str
    doc_id: str
    score: float
    text: str


class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceCitation]
    model: str
