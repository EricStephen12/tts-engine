from fastapi.testclient import TestClient

from api.main import create_app


def test_voices_endpoint_rejects_missing_api_key(fake_model_manager):
    app = create_app()
    client = TestClient(app)
    resp = client.get("/api/v1/voices")
    assert resp.status_code == 401


def test_voices_endpoint_rejects_wrong_api_key(fake_model_manager):
    app = create_app()
    client = TestClient(app)
    resp = client.get("/api/v1/voices", headers={"X-API-Key": "wrong-key"})
    assert resp.status_code == 401


def test_voices_endpoint_accepts_valid_api_key(fake_model_manager):
    app = create_app()
    client = TestClient(app)
    resp = client.get("/api/v1/voices", headers={"X-API-Key": "test-key"})
    assert resp.status_code == 200
    assert "af_heart" in resp.json()["voices"]
