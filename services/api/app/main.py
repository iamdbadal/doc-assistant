import logging
from fastapi import FastAPI, Request
from app.settings import settings

# Basic structured logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.project_name)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Completed request with status: {response.status_code}")
    return response

@app.get("/health")
async def health_check():
    return {"status": "ok", "project": settings.project_name}