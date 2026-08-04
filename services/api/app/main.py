import json
import logging

from fastapi import FastAPI, Request

from app.settings import settings


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