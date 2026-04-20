from contextlib import asynccontextmanager
import uuid
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi import _rate_limit_exceeded_handler

from backend.api.routes import limiter, router as api_router
from backend.api.websocket import manager, router as ws_router
from backend.core.config import settings
from backend.services.email_intel import email_intel_service
from backend.utils.cache import close_cache
from backend.utils.logging import get_logger, sanitize_headers

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await manager.close_all()
    await email_intel_service.aclose()
    await close_cache()


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def secure_logging_middleware(request: Request, call_next):
    """Log sanitized request metadata and return correlation IDs for unexpected server errors."""
    request_payload: dict[str, Any] | None = None

    request_headers = sanitize_headers(dict(request.headers))
    logger.info(
        "request",
        extra={"method": request.method, "path": request.url.path, "headers": request_headers, "payload": request_payload},
    )

    try:
        response = await call_next(request)
    except Exception:
        error_id = str(uuid.uuid4())
        logger.exception(
            "Unhandled server error",
            extra={"error_id": error_id, "method": request.method, "path": request.url.path},
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "An unexpected error occurred. Please try again.", "error_id": error_id},
        )

    logger.info(
        "response",
        extra={"method": request.method, "path": request.url.path, "status_code": response.status_code},
    )
    return response

app.include_router(api_router, prefix="/api/v1", tags=["scan"])
app.include_router(ws_router, prefix="/ws", tags=["ws"])


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
