import logging

import httpx
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)


def is_retriable_error(exc: Exception) -> bool:
    if isinstance(exc, httpx.HTTPStatusError) and exc.response is not None:
        return exc.response.status_code in {429, 500, 502, 503, 504}
    return isinstance(exc, httpx.RequestError)


osint_retry = retry(
    retry=retry_if_exception(is_retriable_error),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    stop=stop_after_attempt(3),
    reraise=True,
    before_sleep=lambda s: logger.warning("Retrying external OSINT call, attempt=%s", s.attempt_number),
)
