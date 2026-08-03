"""Simple API key authentication for service-to-service calls (Node.js -> Python).

Uses a header (`X-API-Key`) rather than OAuth/JWT because the caller is a
trusted backend service, not an end user's browser. Node.js is expected to
hold the key as a server-side secret and never expose it to the client.
"""
from __future__ import annotations

from fastapi import Header, HTTPException, status

from config.settings import get_settings


async def require_api_key(x_api_key: str | None = Header(default=None)) -> str:
    settings = get_settings()
    valid_keys = settings.api_key_list

    if not valid_keys:
        # Explicit opt-out only if no keys are configured at all (dev mode).
        return "anonymous"

    if not x_api_key or x_api_key not in valid_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid API key.",
        )
    return x_api_key
