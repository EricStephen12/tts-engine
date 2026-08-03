"""FastAPI application factory for the Eixora TTS engine."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from api.middleware.logging_middleware import RequestLoggingMiddleware
from api.middleware.rate_limit import limiter
from api.routes import health, metrics, tts, voices
from config.logging_config import configure_logging, get_logger
from config.settings import get_settings
from models.model_manager import get_model_manager
from utils.exceptions import TTSBaseError

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    settings = get_settings()
    manager = get_model_manager()
    try:
        manager.load()
    except Exception as exc:  # noqa: BLE001
        # Do not crash the process: /health will report `degraded` and the
        # synthesis endpoints will return 503 until weights are available.
        logger.error("startup_model_load_failed", error=str(exc))
    logger.info("app_started", host=settings.host, port=settings.port, device=manager.device)
    yield
    logger.info("app_shutdown")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Eixora TTS Engine",
        version="0.1.0",
        description="Proprietary, self-hosted text-to-speech service.",
        lifespan=lifespan,
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestLoggingMiddleware)

    @app.exception_handler(TTSBaseError)
    async def tts_error_handler(request: Request, exc: TTSBaseError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.http_status,
            content={"error_code": exc.error_code, "message": exc.message},
        )

    app.include_router(health.router)
    app.include_router(metrics.router)
    app.include_router(voices.router)
    app.include_router(tts.router)

    return app


app = create_app()
