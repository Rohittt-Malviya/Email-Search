import asyncio
import uuid

from fastapi import APIRouter, BackgroundTasks, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.api.websocket import notify_client
from backend.models.schemas import ScanRequest, ScanResponse
from backend.services.email_intel import email_intel_service
from backend.utils.cache import build_cache_key, get_cached_result, set_cached_result

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


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
    except Exception as exc:
        await notify_client(scan_id, {"status": "failed", "error": str(exc)})


@router.post("/scan", response_model=ScanResponse)
@limiter.limit("5/minute")
async def initiate_scan(request: Request, payload: ScanRequest, background_tasks: BackgroundTasks) -> ScanResponse:
    cache_key = build_cache_key(payload.target_type, payload.target)
    cached = await get_cached_result(cache_key)
    if cached:
        return ScanResponse(scan_id="cached", status="complete", message="Retrieved from cache.")

    scan_id = str(uuid.uuid4())
    background_tasks.add_task(run_osint_pipeline, scan_id, payload.target, payload.target_type)
    return ScanResponse(scan_id=scan_id, status="accepted", message="Scan initiated. Connect to WebSocket feed.")
