# ──────────────────────────────────────────────────────────────────────────────
# Eixora TTS Engine — Railway-compatible Dockerfile
#
# Stages:
#   1. deps   — install Python packages into a prefix we can copy out
#   2. final  — slim runtime image; copy deps, bake model weights, run as non-root
#
# Build:   docker build -t eixora-tts .
# Run:     docker run -p 8100:8100 --env-file .env eixora-tts
# ──────────────────────────────────────────────────────────────────────────────

# ── Stage 1: install dependencies ─────────────────────────────────────────────
FROM python:3.11-slim AS deps

# system libs needed at pip-install time (e.g. soundfile → libsndfile1)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libsndfile1 \
        espeak-ng \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /install

COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --prefix=/install/pkg --no-cache-dir -r requirements.txt


# ── Stage 2: final slim runtime ───────────────────────────────────────────────
FROM python:3.11-slim AS final

# runtime system deps (espeak-ng required by kokoro-onnx / phonemizer)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libsndfile1 \
        espeak-ng \
        curl \
    && rm -rf /var/lib/apt/lists/*

# non-root user (uid 1000) required by Railway and general best-practice
RUN groupadd --gid 1000 appuser \
 && useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

WORKDIR /app

# copy installed packages from build stage
COPY --from=deps /install/pkg /usr/local

# copy application source (models/*.py must be in git — see .gitignore)
COPY --chown=appuser:appuser . .

# int8 weights: smaller image + faster CPU inference on Railway
RUN python scripts/download_models.py --quantized \
 && chown -R appuser:appuser /app/models/weights

# Point settings at the quantized weights baked above (overridable via Railway vars)
ENV TTS_MODEL_PATH=models/weights/kokoro-v1.0.int8.onnx \
    TTS_VOICES_PATH=models/weights/voices-v1.0.bin \
    PYTHONPATH=/app

EXPOSE 8100

COPY --chown=appuser:appuser entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Switch to non-root user for runtime
USER appuser

# Railway injects $PORT; local runs fall back to 8100
CMD ["/app/entrypoint.sh"]
