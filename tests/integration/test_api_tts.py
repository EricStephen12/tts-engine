import base64
import json

from fastapi.testclient import TestClient

from api.main import create_app

HEADERS = {"X-API-Key": "test-key"}


def test_tts_endpoint_returns_wav_audio(fake_model_manager):
    app = create_app()
    client = TestClient(app)
    resp = client.post("/api/v1/tts", json={"text": "Hello world."}, headers=HEADERS)
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "audio/wav"
    assert resp.content[:4] == b"RIFF"
    assert float(resp.headers["x-real-time-factor"]) >= 0


def test_tts_endpoint_rejects_empty_text(fake_model_manager):
    app = create_app()
    client = TestClient(app)
    resp = client.post("/api/v1/tts", json={"text": ""}, headers=HEADERS)
    assert resp.status_code == 422


def test_tts_endpoint_rejects_invalid_voice(fake_model_manager):
    app = create_app()
    client = TestClient(app)
    resp = client.post(
        "/api/v1/tts", json={"text": "Hi.", "voice": "nonexistent"}, headers=HEADERS
    )
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "invalid_voice"


def test_tts_endpoint_rejects_too_long_text(fake_model_manager):
    app = create_app()
    client = TestClient(app)
    resp = client.post(
        "/api/v1/tts", json={"text": "word " * 2000}, headers=HEADERS
    )
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "text_too_long"


def test_tts_stream_endpoint_emits_ndjson_events(fake_model_manager):
    app = create_app()
    client = TestClient(app)
    resp = client.post(
        "/api/v1/tts/stream",
        json={"text": "First sentence. Second sentence."},
        headers=HEADERS,
    )
    assert resp.status_code == 200
    lines = [json.loads(line) for line in resp.text.strip().split("\n")]

    assert lines[0]["type"] == "start"
    assert lines[0]["sample_rate"] == 24000

    audio_events = [line for line in lines if line["type"] == "audio_chunk"]
    assert len(audio_events) == 2
    assert audio_events[-1]["is_final"] is True

    # Verify base64 audio payload decodes to valid PCM16 bytes.
    raw = base64.b64decode(audio_events[0]["data"])
    assert len(raw) % 2 == 0

    assert lines[-1]["type"] == "end"
    assert lines[-1]["total_segments"] == 2
