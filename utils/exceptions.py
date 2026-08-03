"""Domain-specific exceptions for the TTS engine.

Keeping these distinct from generic exceptions lets the API layer map each
one to a precise HTTP status code and error payload.
"""
from __future__ import annotations


class TTSBaseError(Exception):
    """Base class for all TTS engine errors."""

    http_status: int = 500
    error_code: str = "internal_error"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class ModelNotLoadedError(TTSBaseError):
    http_status = 503
    error_code = "model_not_loaded"


class ModelWeightsMissingError(TTSBaseError):
    http_status = 503
    error_code = "model_weights_missing"


class TextTooLongError(TTSBaseError):
    http_status = 422
    error_code = "text_too_long"


class EmptyTextError(TTSBaseError):
    http_status = 422
    error_code = "empty_text"


class InvalidVoiceError(TTSBaseError):
    http_status = 422
    error_code = "invalid_voice"


class InvalidEmotionError(TTSBaseError):
    http_status = 422
    error_code = "invalid_emotion"


class SynthesisError(TTSBaseError):
    http_status = 500
    error_code = "synthesis_failed"
