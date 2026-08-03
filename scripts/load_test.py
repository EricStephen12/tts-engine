"""Locust load test for the TTS REST and streaming endpoints.

Run:
    locust -f scripts/load_test.py --host http://localhost:8100
Then open http://localhost:8089 to configure users/spawn rate.
"""
from __future__ import annotations

import os

from locust import HttpUser, between, task

API_KEY = os.environ.get("TTS_LOAD_TEST_API_KEY", "change-me-dev-key")

SAMPLE_TEXTS = [
    "Hello, welcome to Eixora. This is a quick synthesis test.",
    "Our text to speech engine supports streaming, emotion, and natural pauses.",
    "Stop scrolling. This is the ad hook that gets three x the click through rate.",
]


class TTSUser(HttpUser):
    wait_time = between(1, 3)

    def _headers(self) -> dict:
        return {"X-API-Key": API_KEY, "Content-Type": "application/json"}

    @task(3)
    def synthesize_full(self):
        text = SAMPLE_TEXTS[self.environment.runner.user_count % len(SAMPLE_TEXTS)]
        self.client.post(
            "/api/v1/tts",
            json={"text": text, "emotion": "neutral"},
            headers=self._headers(),
            name="/api/v1/tts",
        )

    @task(1)
    def synthesize_stream(self):
        text = SAMPLE_TEXTS[0]
        with self.client.post(
            "/api/v1/tts/stream",
            json={"text": text},
            headers=self._headers(),
            name="/api/v1/tts/stream",
            stream=True,
            catch_response=True,
        ) as resp:
            for _ in resp.iter_lines():
                pass
            resp.success()

    @task(1)
    def health(self):
        self.client.get("/health", name="/health")
