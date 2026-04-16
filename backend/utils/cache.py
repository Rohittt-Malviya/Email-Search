import hashlib
import json
import logging
from typing import Any

import redis.asyncio as redis

from backend.core.config import settings

logger = logging.getLogger(__name__)

CACHE_TTL_SECONDS = 900
redis_client = redis.from_url(settings.redis_url, decode_responses=True)


def build_cache_key(target_type: str, target: str) -> str:
    digest = hashlib.sha256(f"{target_type}:{target}".encode("utf-8")).hexdigest()
    return f"scan:{digest}"


async def get_cached_result(key: str) -> dict[str, Any] | None:
    try:
        data = await redis_client.get(key)
        return json.loads(data) if data else None
    except Exception:
        logger.exception("Redis get failed")
        return None


async def set_cached_result(key: str, value: dict[str, Any], ttl: int = CACHE_TTL_SECONDS) -> None:
    try:
        await redis_client.setex(key, ttl, json.dumps(value))
    except Exception:
        logger.exception("Redis set failed")


async def close_cache() -> None:
    await redis_client.aclose()
