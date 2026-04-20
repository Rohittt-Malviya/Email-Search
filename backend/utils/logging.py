import logging
from collections.abc import Mapping
from typing import Any

SENSITIVE_HEADERS = {"authorization", "hibp-api-key", "x-api-key", "cookie", "set-cookie"}
SENSITIVE_FIELDS = {"password", "token", "secret", "api_key", "apikey"}
REDACTED = "***REDACTED***"


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def sanitize_headers(headers: Mapping[str, str]) -> dict[str, str]:
    return {key: (REDACTED if key.lower() in SENSITIVE_HEADERS else value) for key, value in headers.items()}


def sanitize_payload(payload: Any) -> Any:
    if isinstance(payload, dict):
        sanitized: dict[str, Any] = {}
        for key, value in payload.items():
            if any(marker in key.lower() for marker in SENSITIVE_FIELDS):
                sanitized[key] = REDACTED
            else:
                sanitized[key] = sanitize_payload(value)
        return sanitized
    if isinstance(payload, list):
        return [sanitize_payload(item) for item in payload]
    return payload
