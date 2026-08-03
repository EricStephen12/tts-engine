from __future__ import annotations

from fastapi import APIRouter, Depends

from api.middleware.auth import require_api_key
from api.schemas.tts import VoiceListResponse
from config.settings import get_settings
from models.model_manager import get_model_manager

router = APIRouter(prefix="/api/v1", tags=["voices"])


@router.get("/voices", response_model=VoiceListResponse, dependencies=[Depends(require_api_key)])
async def list_voices() -> VoiceListResponse:
    manager = get_model_manager()
    settings = get_settings()
    return VoiceListResponse(voices=manager.list_voices(), default_voice=settings.default_voice)
