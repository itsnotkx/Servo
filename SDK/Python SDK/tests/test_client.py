from __future__ import annotations

import pytest

from servo_sdk import Servo
from servo_sdk.errors import ServoAPIError
from servo_sdk.types import ComplexityLevel


def test_send_parses_processing_result(monkeypatch):
    client = Servo(api_key="k", base_url="http://x")

    def fake_request_json(method, path, json_body=None):
        assert method == "POST"
        assert path == "/process"
        assert "prompt" in (json_body or {})
        return {
            "classification": {
                "complexity": "simple",
                "reasoning": "x",
                "requires_chunking": False,
                "suggested_model_tier": "simple",
                "confidence": 0.9,
            },
            "target_model": "qwen-1.5b",
            "chunks": None,
            "chunk_metadata": None,
            "requires_aggregation": False,
        }

    monkeypatch.setattr(client._http, "request_json", fake_request_json)
    result = client.send("hi")
    assert result.target_model == "qwen-1.5b"
    assert result.classification.complexity == ComplexityLevel.SIMPLE


def test_non_2xx_raises(monkeypatch):
    client = Servo(api_key=None, base_url="http://x")

    def fake_request_json(method, path, json_body=None):
        raise ServoAPIError(message="boom", status_code=500, body={"detail": "boom"})

    monkeypatch.setattr(client._http, "request_json", fake_request_json)

    with pytest.raises(ServoAPIError):
        client.health()
