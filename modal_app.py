"""
Eixora Kokoro TTS on Modal (GPU).

One-time setup:
  pip install modal
  python -m modal setup
  modal secret create eixora-tts TTS_API_KEYS=<same-as-server-TTS_ENGINE_API_KEY>

Deploy / iterate:
  modal deploy modal_app.py
  modal serve modal_app.py

Then point the Express server at the printed HTTPS URL:
  TTS_ENGINE_URL=https://<workspace>--eixora-tts-web.modal.run
  TTS_ENGINE_API_KEY=<same key>
  TTS_PROVIDER=kokoro
"""
from __future__ import annotations

from pathlib import Path

import modal

ROOT = Path(__file__).resolve().parent
RELEASE = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0"

app = modal.App("eixora-tts")

tts_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("libsndfile1", "espeak-ng", "curl")
    .pip_install_from_requirements(str(ROOT / "requirements.txt"))
    .run_commands(
        "pip uninstall -y onnxruntime || true",
        # 1.20.1 has no GPU wheel on Modal's index — pin a nearby available build
        "pip install --no-cache-dir onnxruntime-gpu==1.20.2",
        "mkdir -p /root/models/weights",
        f"curl -fsSL -o /root/models/weights/kokoro-v1.0.onnx {RELEASE}/kokoro-v1.0.onnx",
        f"curl -fsSL -o /root/models/weights/voices-v1.0.bin {RELEASE}/voices-v1.0.bin",
    )
    .env(
        {
            "PYTHONPATH": "/root",
            "TTS_DEVICE": "cuda",
            "TTS_MODEL_PATH": "models/weights/kokoro-v1.0.onnx",
            "TTS_VOICES_PATH": "models/weights/voices-v1.0.bin",
            "TTS_CORS_ORIGINS": "*",
            "TTS_LOG_JSON": "true",
        }
    )
    .add_local_dir(
        local_path=str(ROOT),
        remote_path="/root",
        ignore=[
            "**/__pycache__",
            "**/.git",
            "**/.venv",
            "**/models/weights/**",
            "**/tests/**",
            "**/.pytest_cache/**",
            "**/tmp_*",
            "**/*.pyc",
        ],
    )
)


@app.function(
    image=tts_image,
    gpu="T4",
    timeout=300,
    scaledown_window=180,
    memory=4096,
    secrets=[modal.Secret.from_name("eixora-tts")],
)
@modal.concurrent(max_inputs=4)
@modal.asgi_app()
def web():
    import os

    os.chdir("/root")
    from api.main import app as fastapi_app

    return fastapi_app
