"""Downloads Kokoro-82M ONNX model weights and voice pack into models/weights/.

Usage:
    python scripts/download_models.py            # fp32 model (~330MB, best quality)
    python scripts/download_models.py --quantized  # int8 model (~88MB, faster on CPU)
"""
from __future__ import annotations

import argparse
import sys
import urllib.request
from pathlib import Path

RELEASE_BASE = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0"
DEST_DIR = Path(__file__).resolve().parent.parent / "models" / "weights"

FILES = {
    "fp32": ("kokoro-v1.0.onnx", f"{RELEASE_BASE}/kokoro-v1.0.onnx"),
    "int8": ("kokoro-v1.0.int8.onnx", f"{RELEASE_BASE}/kokoro-v1.0.int8.onnx"),
}
VOICES_FILE = ("voices-v1.0.bin", f"{RELEASE_BASE}/voices-v1.0.bin")


def _download(url: str, dest: Path) -> None:
    print(f"Downloading {url} -> {dest}")
    dest.parent.mkdir(parents=True, exist_ok=True)

    def _report(block_num: int, block_size: int, total_size: int) -> None:
        if total_size <= 0:
            return
        downloaded = block_num * block_size
        pct = min(100, downloaded * 100 // total_size)
        print(f"\r  {pct}% ({downloaded // 1_000_000}MB / {total_size // 1_000_000}MB)", end="")

    urllib.request.urlretrieve(url, dest, reporthook=_report)
    print()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quantized", action="store_true", help="Download the int8 quantized model (smaller, faster on CPU).")
    parser.add_argument("--force", action="store_true", help="Re-download even if files already exist.")
    args = parser.parse_args()

    variant = "int8" if args.quantized else "fp32"
    model_name, model_url = FILES[variant]
    voices_name, voices_url = VOICES_FILE

    model_dest = DEST_DIR / model_name
    voices_dest = DEST_DIR / voices_name

    if model_dest.exists() and not args.force:
        print(f"Model already present at {model_dest}, skipping (use --force to re-download).")
    else:
        _download(model_url, model_dest)

    if voices_dest.exists() and not args.force:
        print(f"Voices already present at {voices_dest}, skipping (use --force to re-download).")
    else:
        _download(voices_url, voices_dest)

    canonical_model = DEST_DIR / "kokoro-v1.0.onnx"
    if variant == "int8" and not canonical_model.exists():
        print(
            "NOTE: you downloaded the int8 model. Set TTS_MODEL_PATH="
            f"models/weights/{model_name} in your .env (or rename the file) "
            "so the server picks it up."
        )

    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
