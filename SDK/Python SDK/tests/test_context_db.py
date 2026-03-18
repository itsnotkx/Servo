from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from servo_sdk.client import ContextDB
from servo_sdk import (
    ServoEmbeddingError,
    ContextualizedSubtask,
    ContextualizedDecompositionResult,
    ClassifiedSubtask,
    ClassifiedDecompositionResult,
    Servo,
)


# ---------------------------------------------------------------------------
# Shared fixture: real fastembed embedding function (cached across tests)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def embedding_fn():
    from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
    return DefaultEmbeddingFunction()


# ---------------------------------------------------------------------------
# ContextDB unit tests
# ---------------------------------------------------------------------------

def test_context_db_add_and_retrieve(embedding_fn):
    db = ContextDB(embedding_fn)
    db.add("task-1", "Write a summary of the document")
    assert db.get_by_id("task-1") == "Write a summary of the document"
    assert db.get_context_for(["task-1"]) == ["Write a summary of the document"]
    assert db.get_context_for(["nonexistent"]) == []


def test_context_db_overwrite(embedding_fn):
    db = ContextDB(embedding_fn)
    db.add("task-1", "original subtask text")
    db.add("task-1", "model response after routing")  # Stage 5 overwrite
    assert db.get_by_id("task-1") == "model response after routing"


def test_context_db_search(embedding_fn):
    db = ContextDB(embedding_fn)
    db.add("task-1", "summarize the report")
    db.add("task-2", "translate the document to French")
    results = db.search("create a summary", k=1)
    assert len(results) == 1  # should return semantically nearest


def test_context_db_search_empty(embedding_fn):
    db = ContextDB(embedding_fn)
    results = db.search("anything", k=3)
    assert results == []


def test_context_db_get_context_for_empty_list(embedding_fn):
    db = ContextDB(embedding_fn)
    db.add("task-1", "some text")
    assert db.get_context_for([]) == []


def test_context_db_get_by_id_missing(embedding_fn):
    db = ContextDB(embedding_fn)
    assert db.get_by_id("does-not-exist") is None


# ---------------------------------------------------------------------------
# Pipeline integration tests (embed_and_contextualize)
# ---------------------------------------------------------------------------

def _make_classified_result() -> ClassifiedDecompositionResult:
    return ClassifiedDecompositionResult(
        subtasks=[
            ClassifiedSubtask(
                id="task-A",
                text="Fetch the data",
                depends_on=[],
                complexity_id="simple",
                complexity_reasoning="straightforward retrieval",
            ),
            ClassifiedSubtask(
                id="task-B",
                text="Summarise the fetched data",
                depends_on=["task-A"],
                complexity_id="medium",
                complexity_reasoning="requires synthesis",
            ),
        ]
    )


def _make_servo_client(monkeypatch) -> Servo:
    monkeypatch.setattr(Servo, "__post_init__", lambda self: None)
    client = Servo(api_key="sk_live_test")
    client._cached_config = MagicMock()
    client._default_conversation = None
    client._classifier_url = "http://localhost:8080"
    client._embedding_fn_cache = None
    return client


def test_embed_and_contextualize_empty_context(monkeypatch, embedding_fn):
    """All subtasks have empty context lists after embed_and_contextualize."""
    client = _make_servo_client(monkeypatch)
    client._embedding_fn_cache = embedding_fn

    classified = _make_classified_result()
    result, db = client.embed_and_contextualize(classified)

    assert isinstance(result, ContextualizedDecompositionResult)
    assert all(st.context == [] for st in result.subtasks)


def test_embed_and_contextualize_texts_in_db(monkeypatch, embedding_fn):
    """Subtask texts are retrievable from the returned ContextDB."""
    client = _make_servo_client(monkeypatch)
    client._embedding_fn_cache = embedding_fn

    classified = _make_classified_result()
    result, db = client.embed_and_contextualize(classified)

    assert db.get_by_id("task-A") == "Fetch the data"
    assert db.get_by_id("task-B") == "Summarise the fetched data"


def test_embed_and_contextualize_stage5_simulation(monkeypatch, embedding_fn):
    """Simulate Stage 5: store a response for task-A, then retrieve it as context for task-B."""
    client = _make_servo_client(monkeypatch)
    client._embedding_fn_cache = embedding_fn

    classified = _make_classified_result()
    result, db = client.embed_and_contextualize(classified)

    # Stage 5 stores task-A's response
    db.add("task-A", "Here is the fetched data: [...]")
    ctx = db.get_context_for(["task-A"])
    assert ctx == ["Here is the fetched data: [...]"]


# ---------------------------------------------------------------------------
# Caching test: _embedding_fn returns same object
# ---------------------------------------------------------------------------

def test_embedding_fn_cached(monkeypatch):
    """_embedding_fn returns the same object on repeated access."""
    client = _make_servo_client(monkeypatch)
    fn1 = client._embedding_fn
    fn2 = client._embedding_fn
    assert fn1 is fn2
