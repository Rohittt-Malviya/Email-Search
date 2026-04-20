from contextlib import asynccontextmanager
import json

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
from backend.utils.logging import get_logger, sanitize_headers, sanitize_payload

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
    body = await request.body()
    request_payload: object | str = {}
    if body:
        try:
            request_payload = sanitize_payload(json.loads(body))
        except json.JSONDecodeError:
            request_payload = "<non-json>"

    request_headers = sanitize_headers(dict(request.headers))
    logger.info(
        "request",
        extra={"method": request.method, "path": request.url.path, "headers": request_headers, "payload": request_payload},
    )

    consumed = False

    async def receive() -> dict[str, object]:
        nonlocal consumed
        if consumed:
            return {"type": "http.request", "body": b"", "more_body": False}
        consumed = True
        return {"type": "http.request", "body": body, "more_body": False}

    request._receive = receive  # type: ignore[attr-defined]

    try:
        response = await call_next(request)
    except Exception:
        logger.exception("Unhandled server error", extra={"method": request.method, "path": request.url.path})
        return JSONResponse(status_code=500, content={"detail": "An unexpected error occurred. Please try again."})

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
