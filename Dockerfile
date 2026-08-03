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
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /install

COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --prefix=/install/pkg --no-cache-dir -r requirements.txt


# ── Stage 2: final slim runtime ───────────────────────────────────────────────
FROM python:3.11-slim AS final

# runtime system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
        libsndfile1 \
        curl \
    && rm -rf /var/lib/apt/lists/*

# non-root user (uid 1000) required by Railway and general best-practice
RUN groupadd --gid 1000 appuser \
 && useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

WORKDIR /app

# copy installed packages from build stage
COPY --from=deps /install/pkg /usr/local

# copy application source
COPY --chown=appuser:appuser . .

# download model weights into the image at build time so the container is
# self-contained and ready on first boot (idempotent — skips if already present)
RUN python scripts/download_models.py

EXPOSE 8100

# Switch to non-root user for runtime
USER appuser

# Railway injects $PORT; local runs fall back to 8100
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8100}"]
