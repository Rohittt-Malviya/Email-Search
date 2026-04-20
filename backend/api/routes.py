import asyncio
import hashlib
import time
import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.api.websocket import notify_client
from backend.models.schemas import ScanRequest, ScanResponse
from backend.services.email_intel import email_intel_service
from backend.utils.cache import build_cache_key, get_cached_result, set_cached_result
from backend.utils.logging import get_logger

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
logger = get_logger(__name__)

CLIENT_LIMIT_PER_MINUTE = 5
TARGET_LIMIT_PER_HOUR = 20
_rate_limit_state: dict[str, tuple[int, float]] = {}


def _increment_counter(key: str, limit: int, window_seconds: int) -> bool:
    now = time.monotonic()
    if len(_rate_limit_state) > 5000:
        expired_keys = [state_key for state_key, (_, window_end) in _rate_limit_state.items() if now >= window_end]
        for expired_key in expired_keys:
            _rate_limit_state.pop(expired_key, None)

    count, window_end = _rate_limit_state.get(key, (0, now + window_seconds))
    if now >= window_end:
        count, window_end = 0, now + window_seconds

    count += 1
    _rate_limit_state[key] = (count, window_end)
    return count <= limit


def _enforce_multi_level_limits(request: Request, payload: ScanRequest) -> None:
    ip = get_remote_address(request)
    user_agent = request.headers.get("user-agent", "unknown")
    target_fingerprint = hashlib.sha256(f"{payload.target_type}:{payload.target}".encode("utf-8")).hexdigest()

    client_key = f"rl:client:{hashlib.sha256(f'{ip}:{user_agent}:{target_fingerprint}'.encode('utf-8')).hexdigest()}"
    target_key = f"rl:target:{target_fingerprint}"

    client_allowed = _increment_counter(client_key, CLIENT_LIMIT_PER_MINUTE, 60)
    target_allowed = _increment_counter(target_key, TARGET_LIMIT_PER_HOUR, 3600)

    if not client_allowed or not target_allowed:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please retry later.")


async def run_osint_pipeline(scan_id: str, target: str, target_type: str) -> None:
    try:
        await notify_client(scan_id, {"status": "processing", "step": "Initializing scan modules"})

        if target_type == "email":
            await notify_client(scan_id, {"status": "processing", "step": "Running HIBP and presence checks"})
            hibp_task = email_intel_service.check_hibp(target)
            presence_task = email_intel_service.check_presence(target)
            hibp_result, presence_result = await asyncio.gather(hibp_task, presence_task, return_exceptions=True)

            result = {
                "breach_data": hibp_result if not isinstance(hibp_result, Exception) else {"status": "error"},
                "account_presence": (
                    presence_result if not isinstance(presence_result, Exception) else {"status": "error"}
                ),
            }
        else:
            await notify_client(scan_id, {"status": "processing", "step": "Phone intelligence is simulated"})
            result = {"phone_intel": {"status": "simulated", "target": target}}

        await set_cached_result(build_cache_key(target_type, target), result)
        await notify_client(scan_id, {"status": "complete", "data": result})
    except Exception:
        logger.exception("Scan pipeline failed", extra={"scan_id": scan_id, "target_type": target_type})
        await notify_client(scan_id, {"status": "failed", "error": "Scan failed due to an upstream service issue."})


@router.post("/scan", response_model=ScanResponse)
@limiter.limit("5/minute")
async def initiate_scan(request: Request, payload: ScanRequest, background_tasks: BackgroundTasks) -> ScanResponse:
    _enforce_multi_level_limits(request, payload)

    cache_key = build_cache_key(payload.target_type, payload.target)
    cached = await get_cached_result(cache_key)
    if cached:
        return ScanResponse(scan_id="cached", status="complete", message="Retrieved from cache.")

    scan_id = str(uuid.uuid4())
    background_tasks.add_task(run_osint_pipeline, scan_id, payload.target, payload.target_type)
    return ScanResponse(scan_id=scan_id, status="accepted", message="Scan initiated. Connect to WebSocket feed.")
