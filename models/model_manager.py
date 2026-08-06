"""Loads and manages the Kokoro-82M ONNX model as a process-wide singleton.

Device selection (CPU vs GPU) is handled entirely through the ONNX Runtime
execution provider list -- there is exactly one inference code path, which
keeps the CPU and GPU deployments identical apart from the Docker base
image and installed `onnxruntime` variant.
"""
from __future__ import annotations

import threading

import os
from config.settings import Settings, get_settings
from config.logging_config import get_logger
from utils.exceptions import ModelWeightsMissingError

logger = get_logger(__name__)

_lock = threading.Lock()
_instance: "ModelManager | None" = None


class ModelManager:
    """Owns the loaded Kokoro pipeline and exposes voice metadata."""

    def __init__(self, settings: Settings):
        self._settings = settings
        self._kokoro = None
        self._device = "cpu"

    @property
    def device(self) -> str:
        return self._device

    @property
    def is_loaded(self) -> bool:
        return self._kokoro is not None

    def load(self) -> None:
        if self._kokoro is not None:
            return

        model_path = self._settings.resolved_model_path
        voices_path = self._settings.resolved_voices_path

        if not model_path.exists() or not voices_path.exists():
            raise ModelWeightsMissingError(
                "Kokoro model weights not found. Run "
                "`python scripts/download_models.py` first. Expected files: "
                f"{model_path}, {voices_path}"
            )

        providers = self._resolve_providers()
        logger.info("model_loading", providers=providers, model_path=str(model_path))

        from kokoro_onnx import Kokoro

        last_error: Exception | None = None
        import onnxruntime as ort
        available_providers = ort.get_available_providers()

        for provider_name, device_label in providers:
            if provider_name not in available_providers:
                if provider_name == "CUDAExecutionProvider":
                    logger.warning(
                        "provider_unavailable",
                        provider=provider_name,
                        available=available_providers,
                    )
                    continue

            env_key = "ONNX_PROVIDER"
            previous_provider = os.environ.get(env_key)
            os.environ[env_key] = provider_name
            try:
                self._kokoro = Kokoro(
                    str(model_path),
                    str(voices_path),
                )
                self._device = device_label
                logger.info("model_loaded", device=device_label, provider=provider_name)
                return
            except Exception as exc:  # pragma: no cover - hardware dependent
                last_error = exc
                logger.warning(
                    "model_load_failed_for_provider",
                    provider=provider_name,
                    error=str(exc),
                )
                self._kokoro = None
            finally:
                if previous_provider is None:
                    os.environ.pop(env_key, None)
                else:
                    os.environ[env_key] = previous_provider

        raise ModelWeightsMissingError(
            f"Failed to load Kokoro model with any provider: {last_error}"
        )

    def _resolve_providers(self) -> list[tuple[str, str]]:
        requested = self._settings.device
        if requested == "cpu":
            return [("CPUExecutionProvider", "cpu")]
        if requested == "cuda":
            return [("CUDAExecutionProvider", "cuda")]
        # auto: try CUDA first, gracefully fall back to CPU.
        return [
            ("CUDAExecutionProvider", "cuda"),
            ("CPUExecutionProvider", "cpu"),
        ]

    def list_voices(self) -> list[str]:
        self._ensure_loaded()
        return sorted(self._kokoro.get_voices())

    def synthesize(self, text: str, voice: str, speed: float, lang: str):
        """Synthesize a single segment of text. Returns (audio: np.ndarray, sample_rate: int)."""
        self._ensure_loaded()
        audio, sample_rate = self._kokoro.create(
            text, voice=voice, speed=speed, lang=lang
        )
        return audio, sample_rate

    def _ensure_loaded(self) -> None:
        if self._kokoro is None:
            raise ModelWeightsMissingError("Model is not loaded yet.")


def get_model_manager() -> ModelManager:
    global _instance
    if _instance is None:
        with _lock:
            if _instance is None:
                _instance = ModelManager(get_settings())
    return _instance


def reset_model_manager() -> None:
    """Test helper: clears the singleton so a fresh instance is built."""
    global _instance
    with _lock:
        _instance = None
