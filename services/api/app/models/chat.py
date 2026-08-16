from typing import Optional

from pydantic import BaseModel


class ChatRequest(BaseModel):
    query: str
    tenant_id: str
    session_id: Optional[str] = None  # If None, a new session is created
    top_k: int = 3
