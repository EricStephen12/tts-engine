from __future__ import annotations

import time

from fastapi import APIRouter

from api.schemas.tts import HealthResponse
from models.model_manager import get_model_manager

router = APIRouter(tags=["health"])
_START_TIME = time.monotonic()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    manager = get_model_manager()
    return HealthResponse(
        status="ok" if manager.is_loaded else "degraded",
        model_loaded=manager.is_loaded,
        device=manager.device,
        uptime_s=round(time.monotonic() - _START_TIME, 1),
    )


@router.get("/", response_model=HealthResponse)
async def root() -> HealthResponse:
    return await health()


@router.get("/health/ready")
async def ready() -> dict:
    manager = get_model_manager()
    return {"ready": manager.is_loaded}
