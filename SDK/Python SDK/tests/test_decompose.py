from __future__ import annotations

import os
import pytest
from unittest.mock import MagicMock, patch

from servo_sdk import Servo, ServoDecompositionError, Subtask, DecompositionResult


def _make_client(monkeypatch, classifier_url: str | None = None) -> Servo:
    """Build a Servo client with __post_init__ bypassed to avoid real HTTP."""
    monkeypatch.setattr(Servo, "__post_init__", lambda self: None)
    client = Servo(api_key="sk_live_test", classifier_url=classifier_url)
    # Manually set internal state that __post_init__ would have set
    client._cached_config = MagicMock(user_id="user-456")
    client._default_conversation = None
    if classifier_url is not None:
        client._classifier_url = classifier_url
    else:
        client._classifier_url = os.environ.get("CLASSIFIER_ENDPOINT", "http://localhost:8080")
    return client


def test_decompose_returns_typed_result(monkeypatch):
    """Mock chain.invoke to return a valid DecompositionResult."""
    client = _make_client(monkeypatch)

    expected = DecompositionResult(
        subtasks=[
            Subtask(id="1", text="Set up project scaffold"),
            Subtask(id="2", text="Implement scraper", dependsOn=["1"]),
        ]
    )

    with patch("servo_sdk.client.ChatOpenAI"), \
         patch("servo_sdk.client.ChatPromptTemplate") as mock_pt:
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = expected
        mock_pt.from_messages.return_value.__or__ = MagicMock(return_value=mock_chain)

        result = client.decompose("Build a web scraper for news articles")

    assert isinstance(result, DecompositionResult)
    assert len(result.subtasks) == 2
    assert result.subtasks[0].id == "1"
    assert result.subtasks[1].depends_on == ["1"]


def test_decompose_raises_on_langchain_exception(monkeypatch):
    """If chain.invoke raises, ServoDecompositionError is raised."""
    client = _make_client(monkeypatch)

    with patch("servo_sdk.client.ChatOpenAI"), \
         patch("servo_sdk.client.ChatPromptTemplate") as mock_pt:
        mock_chain = MagicMock()
        mock_chain.invoke.side_effect = RuntimeError("model timeout")
        mock_pt.from_messages.return_value.__or__ = MagicMock(return_value=mock_chain)

        with pytest.raises(ServoDecompositionError) as exc_info:
            client.decompose("some prompt")

    assert "Decomposition failed" in exc_info.value.message
    assert "model timeout" in exc_info.value.raw_content


def test_decompose_uses_classifier_url_field(monkeypatch):
    """ChatOpenAI is constructed with base_url derived from classifier_url field."""
    client = _make_client(monkeypatch, classifier_url="http://my-classifier:9090")

    captured_kwargs: dict = {}

    def fake_chat_openai(**kwargs):
        captured_kwargs.update(kwargs)
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = MagicMock()
        return mock_llm

    with patch("servo_sdk.client.ChatOpenAI", side_effect=fake_chat_openai), \
         patch("servo_sdk.client.ChatPromptTemplate") as mock_pt:
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = DecompositionResult(subtasks=[])
        mock_pt.from_messages.return_value.__or__ = MagicMock(return_value=mock_chain)

        client.decompose("test prompt")

    assert captured_kwargs["base_url"] == "http://my-classifier:9090/v1"


def test_decompose_uses_env_var(monkeypatch):
    """CLASSIFIER_ENDPOINT env var is used when classifier_url field is not set."""
    monkeypatch.setenv("CLASSIFIER_ENDPOINT", "http://env-classifier:7777")
    client = _make_client(monkeypatch)
    # Re-apply env resolution since __post_init__ was bypassed
    client._classifier_url = os.environ.get("CLASSIFIER_ENDPOINT", "http://localhost:8080")

    captured_kwargs: dict = {}

    def fake_chat_openai(**kwargs):
        captured_kwargs.update(kwargs)
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = MagicMock()
        return mock_llm

    with patch("servo_sdk.client.ChatOpenAI", side_effect=fake_chat_openai), \
         patch("servo_sdk.client.ChatPromptTemplate") as mock_pt:
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = DecompositionResult(subtasks=[])
        mock_pt.from_messages.return_value.__or__ = MagicMock(return_value=mock_chain)

        client.decompose("test prompt")

    assert captured_kwargs["base_url"] == "http://env-classifier:7777/v1"


def test_decompose_subtask_depends_on_alias(monkeypatch):
    """dependsOn JSON alias round-trips correctly via Pydantic."""
    # Construct via alias (camelCase) — as JSON would deliver it
    subtask_via_alias = Subtask.model_validate({"id": "t2", "text": "step 2", "dependsOn": ["t1"]})
    assert subtask_via_alias.depends_on == ["t1"]

    # Construct via snake_case field name
    subtask_via_snake = Subtask(id="t3", text="step 3", depends_on=["t1", "t2"])
    assert subtask_via_snake.depends_on == ["t1", "t2"]

    # Serialise back to JSON — alias is used in output
    dumped = subtask_via_alias.model_dump(by_alias=True)
    assert "dependsOn" in dumped
    assert dumped["dependsOn"] == ["t1"]
