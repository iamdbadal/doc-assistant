import json
import logging
from contextlib import asynccontextmanager

from app.api.auth import get_current_tenant
from app.api.auth import router as auth_router
from app.db.models import Base, engine
from app.settings import settings
from fastapi import Depends, FastAPI, Request


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
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title=settings.project_name,
    version=settings.api_version,
    lifespan=lifespan,
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
