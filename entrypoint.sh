#!/usr/bin/env sh

set -e

PORT=${PORT:-8100}

exec uvicorn api.main:app --host 0.0.0.0 --port "$PORT"
