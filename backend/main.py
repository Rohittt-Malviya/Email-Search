from contextlib import asynccontextmanager

from fastapi import FastAPI
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi import _rate_limit_exceeded_handler

from backend.api.routes import limiter, router as api_router
from backend.api.websocket import manager, router as ws_router
from backend.core.config import settings
from backend.services.email_intel import email_intel_service
from backend.utils.cache import close_cache


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

app.include_router(api_router, prefix="/api/v1", tags=["scan"])
app.include_router(ws_router, prefix="/ws", tags=["ws"])


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
