from __future__ import annotations

import os
import pytest

from servo_sdk import Servo
from servo_sdk.errors import ServoAPIError, ServoAuthenticationError


VALID_VALIDATE_RESPONSE = {
    "valid": True,
    "key_id": "key-123",
    "user_id": "user-456",
    "model": "gemini-3.1-flash-lite",
    "tags": ["prod"],
    "tiers": {"simple": "gemini-2.5-flash-lite", "complex": "gemini-3.1-flash-lite"},
}

VALID_ROUTING_RESPONSE = {
    "default_category_id": "simple",
    "categories": [
        {
            "id": "simple",
            "name": "Simple",
            "description": "Simple queries",
            "provider": "google",
            "endpoint": "https://api.example.com",
            "model_id": "gemini-2.5-flash-lite",
        },
        {
            "id": "complex",
            "name": "Complex",
            "description": "Complex queries",
            "provider": "google",
            "endpoint": "https://api.example.com",
            "model_id": "gemini-3.1-flash-lite",
        },
    ],
}


def _make_client(monkeypatch, validate_resp=None, routing_resp=None, validate_error=None):
    """Helper: build a Servo client with mocked HTTP calls."""
    monkeypatch.setenv("SERVO_ENDPOINT", "http://test-server")

    call_log: list[tuple[str, str]] = []

    def fake_request_json(method, path, json_body=None):
        call_log.append((method, path))

        if path == "/api/sdk/validate":
            if validate_error:
                raise validate_error
            return validate_resp or VALID_VALIDATE_RESPONSE

        if path == "/api/sdk/routing-config":
            if routing_resp is None:
                raise ServoAPIError(message="not found", status_code=404, body=None)
            return routing_resp

        raise AssertionError(f"Unexpected call: {method} {path}")

    # Prevent __post_init__ from running before we patch _http
    monkeypatch.setattr(Servo, "__post_init__", lambda self: None)
    client = Servo(api_key="sk_live_test")
    from servo_sdk._http import HTTPClient
    client._http = HTTPClient(base_url="http://test-server", api_key="sk_live_test", timeout_s=5)
    monkeypatch.setattr(client._http, "request_json", fake_request_json)
    client._cached_config = None
    from servo_sdk.context import Conversation
    client._default_conversation = None
    client._validate_and_cache()

    return client, call_log


def test_init_validates_and_caches(monkeypatch):
    client, call_log = _make_client(
        monkeypatch,
        validate_resp=VALID_VALIDATE_RESPONSE,
        routing_resp=VALID_ROUTING_RESPONSE,
    )
    assert client.config is not None
    assert client.config.key_id == "key-123"
    assert client.config.user_id == "user-456"
    assert client.config.model == "gemini-3.1-flash-lite"
    assert client.config.tags == ["prod"]
    assert client.config.tiers == {"simple": "gemini-2.5-flash-lite", "complex": "gemini-3.1-flash-lite"}
    assert client.user_id == "user-456"

    assert ("POST", "/api/sdk/validate") in call_log
    assert ("GET", "/api/sdk/routing-config") in call_log


def test_init_caches_routing_config(monkeypatch):
    client, _ = _make_client(
        monkeypatch,
        validate_resp=VALID_VALIDATE_RESPONSE,
        routing_resp=VALID_ROUTING_RESPONSE,
    )
    rc = client.config.routing_config
    assert rc is not None
    assert rc.default_category_id == "simple"
    assert len(rc.categories) == 2
    assert rc.categories[0].id == "simple"
    assert rc.categories[1].id == "complex"


def test_init_invalid_key_raises(monkeypatch):
    with pytest.raises(ServoAuthenticationError) as exc_info:
        _make_client(
            monkeypatch,
            validate_error=ServoAPIError(
                message="Invalid API key", status_code=401, body={"error": "Invalid API key"}
            ),
        )
    assert exc_info.value.status_code == 401


def test_init_inactive_key_raises(monkeypatch):
    with pytest.raises(ServoAuthenticationError) as exc_info:
        _make_client(
            monkeypatch,
            validate_error=ServoAPIError(
                message="API key is inactive", status_code=403, body={"error": "API key is inactive"}
            ),
        )
    assert exc_info.value.status_code == 403


def test_init_routing_failure_still_succeeds(monkeypatch):
    """If routing-config returns an error, init still succeeds with routing_config=None."""
    client, _ = _make_client(
        monkeypatch,
        validate_resp=VALID_VALIDATE_RESPONSE,
        routing_resp=None,  # will trigger 404
    )
    assert client.config is not None
    assert client.config.routing_config is None


def test_send_parses_processing_result(monkeypatch):
    client, _ = _make_client(
        monkeypatch,
        validate_resp=VALID_VALIDATE_RESPONSE,
        routing_resp=VALID_ROUTING_RESPONSE,
    )

    def fake_request_json(method, path, json_body=None):
        assert method == "POST"
        assert path == "/process"
        assert "prompt" in (json_body or {})
        return {
            "classification": {
                "category_id": "simple",
                "category_name": "Simple",
                "reasoning": "x",
                "requires_chunking": False,
                "confidence": 0.9,
            },
            "target_model": "gemma-3-27b-it",
            "selected_category": {
                "id": "simple",
                "name": "Simple",
                "description": "",
                "provider": "google",
                "endpoint": "https://api.example.com",
                "model_id": "gemma-3-27b-it",
            },
            "llm_response": "Hello!",
            "chunks": None,
            "chunk_metadata": None,
            "requires_aggregation": False,
        }

    monkeypatch.setattr(client._http, "request_json", fake_request_json)
    result = client.send("hi")
    assert result.target_model == "gemma-3-27b-it"
    assert result.classification.category_id == "simple"


def test_non_2xx_raises(monkeypatch):
    client, _ = _make_client(
        monkeypatch,
        validate_resp=VALID_VALIDATE_RESPONSE,
        routing_resp=VALID_ROUTING_RESPONSE,
    )

    def fake_request_json(method, path, json_body=None):
        raise ServoAPIError(message="boom", status_code=500, body={"detail": "boom"})

    monkeypatch.setattr(client._http, "request_json", fake_request_json)

    with pytest.raises(ServoAPIError):
        client.health()
