"""Centralized application configuration.

All configuration is sourced from environment variables (or a local `.env`
file, see `.env.example`) using `pydantic-settings`. Nothing here should be
hardcoded elsewhere in the codebase -- always depend on `get_settings()`.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="TTS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Server ---
    host: str = "0.0.0.0"
    port: int = 8100
    log_level: str = "INFO"
    log_json: bool = True

    # --- Security ---
    api_keys: str = "change-me-dev-key"
    cors_origins: str = "http://localhost:3000"
    rate_limit: str = "60/minute"

    # --- Model / device ---
    device: str = "auto"  # auto | cpu | cuda
    model_path: str = "models/weights/kokoro-v1.0.onnx"
    voices_path: str = "models/weights/voices-v1.0.bin"
    default_voice: str = "af_heart"
    default_lang: str = "a"
    sample_rate: int = 24000

    # --- Limits ---
    max_text_length: int = 5000

    @field_validator("device")
    @classmethod
    def _validate_device(cls, v: str) -> str:
        allowed = {"auto", "cpu", "cuda"}
        if v not in allowed:
            raise ValueError(f"device must be one of {allowed}, got {v!r}")
        return v

    @property
    def api_key_list(self) -> list[str]:
        return [k.strip() for k in self.api_keys.split(",") if k.strip()]

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def resolved_model_path(self) -> Path:
        p = Path(self.model_path)
        return p if p.is_absolute() else (BASE_DIR / p)

    @property
    def resolved_voices_path(self) -> Path:
        p = Path(self.voices_path)
        return p if p.is_absolute() else (BASE_DIR / p)


@lru_cache
def get_settings() -> Settings:
    """Return a cached, process-wide Settings instance."""
    return Settings()
