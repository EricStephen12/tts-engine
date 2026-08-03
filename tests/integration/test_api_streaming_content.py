"""Verifies the streamed PCM16 audio, once reassembled, is sane audio data
(not just well-formed JSON envelopes)."""
from __future__ import annotations

import base64
import json

from fastapi.testclient import TestClient

from api.main import create_app

HEADERS = {"X-API-Key": "test-key"}


def test_reassembled_stream_matches_full_synthesis_duration(fake_model_manager):
    app = create_app()
    client = TestClient(app)
    text = "First sentence here. Second sentence follows."

    stream_resp = client.post(
        "/api/v1/tts/stream", json={"text": text}, headers=HEADERS
    )
    full_resp = client.post("/api/v1/tts", json={"text": text}, headers=HEADERS)

    lines = [json.loads(line) for line in stream_resp.text.strip().split("\n")]
    sample_rate = lines[0]["sample_rate"]
    audio_events = [line for line in lines if line["type"] == "audio_chunk"]

    total_samples = sum(
        len(base64.b64decode(evt["data"])) // 2 for evt in audio_events
    )
    stream_duration_s = total_samples / sample_rate

    full_duration_s = float(full_resp.headers["x-audio-duration-s"])

    # Streamed duration excludes inter-segment silence (which is only added
    # during full-file concatenation), so it should be close to, but not
    # exceed, the full synthesis duration.
    assert 0 < stream_duration_s <= full_duration_s + 0.1
