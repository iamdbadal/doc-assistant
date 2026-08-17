import json
import logging
from contextlib import asynccontextmanager

from app.api.auth import get_current_tenant
from app.api.auth import router as auth_router

# --- Import the documents router ---
from app.api.documents import router as documents_router

# --- Import the new Chat Streaming router ---
from app.api.v1.endpoints.chat import router as chat_router

# --- Import the query/RAG router ---
# Adjust the import path if your file is named differently (e.g. app.api.rag or app.api.v1.endpoints.query)
from app.api.v1.endpoints.query import router as query_router
from app.db.models import Base, engine
from app.settings import settings
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware  # <-- ADDED THIS IMPORT


class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "time": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        return json.dumps(log_record)


# Setup JSON Logger
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
logger.setLevel(settings.log_level)

# Prevent duplicate logs if running uvicorn
logger.propagate = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Automatically create PostgreSQL tables on application startup
    # This will now include your new ChatSession and ChatMessage tables!
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title=settings.project_name,
    version=settings.api_version,
    lifespan=lifespan,
)

# --- ADDED CORS MIDDLEWARE HERE ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for local Flutter Web testing
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],  # Allows all headers (including Authorization and X-Tenant-ID)
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Completed request with status: {response.status_code}")
    return response


@app.get("/health")
async def health_check():
    return {"status": "ok", "project": settings.project_name}


# Include Auth Router
app.include_router(auth_router)

# --- WEEK 3 ADDITION: Include the Documents Router ---
app.include_router(documents_router)

# --- WEEK 6 ADDITION: Include the Query Router ---
app.include_router(query_router)

# --- WEEK 8 ADDITION: Include the Chat Router ---
app.include_router(chat_router, prefix="/v1/chat", tags=["chat"])


# Protected Tenant Isolation Test Route
@app.get("/v1/me", tags=["tenant-test"])
async def get_tenant_info(
    tenant_id: str = Depends(get_current_tenant),
):
    """
    Requires a valid JWT Access Token.
    Returns the tenant_id extracted from the token's payload.
    """
    return {
        "status": "authenticated",
        "tenant_id": tenant_id,
        "message": "Successfully accessed protected tenant route!",
    }
