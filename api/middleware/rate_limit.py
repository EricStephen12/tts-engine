"""Request rate limiting to protect the (relatively expensive) synthesis
endpoints from abuse or runaway retry loops on the Node.js side.
"""
from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

from config.settings import get_settings


def _key_func(request):
    api_key = request.headers.get("x-api-key")
    return api_key or get_remote_address(request)


limiter = Limiter(key_func=_key_func, default_limits=[get_settings().rate_limit])
