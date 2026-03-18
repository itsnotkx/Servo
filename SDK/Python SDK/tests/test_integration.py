"""
Integration tests for the decompose_and_classify pipeline and Stage 5 route_and_execute.

Classifier tests call the actual classifier running at localhost:8080 (or the URL set
in CLASSIFIER_ENDPOINT).  They are skipped automatically when the classifier is
not reachable, so they are safe to run in CI without a local model server.

Run them explicitly:
    pytest tests/test_integration.py -v -s
"""
from __future__ import annotations

import os
import time
import urllib.request
import urllib.error
from dataclasses import dataclass
from unittest.mock import MagicMock, patch

import pytest

from servo_sdk import (
    ExecutionResult,
    Servo,
    ClassifiedDecompositionResult,
    ClassifiedSubtask,
    RoutingCategory,
    ServoRoutingError,
    SubtaskExecutionResult,
)
from servo_sdk.client import ContextDB
from servo_sdk.types import CachedConfig, ContextualizedDecompositionResult, ContextualizedSubtask, RoutingConfig


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_CLASSIFIER_URL: str = os.environ.get("CLASSIFIER_ENDPOINT", "http://localhost:8080")

_SAMPLE_CATEGORIES = [
    RoutingCategory(
        id="simple",
        name="Simple",
        description="The prompt is straightforward with no multi-step reasoning required",
        model="gemma-3-27b-it",
    ),
    RoutingCategory(
        id="medium",
        name="Medium",
        description="The prompt requires short chain-of-thought or moderate complexity",
        model="gemini-2.5-flash",
    ),
    RoutingCategory(
        id="complex",
        name="Complex",
        description="The prompt requires deep reasoning, planning, or multi-step problem solving",
        model="claude-opus-4-5",
    ),
]


def _classifier_reachable() -> bool:
    """Return True if the classifier health endpoint responds."""
    try:
        with urllib.request.urlopen(
            _CLASSIFIER_URL.rstrip("/") + "/health", timeout=2
        ):
            return True
    except Exception:
        return False


def _make_integration_client() -> Servo:
    """
    Build a Servo client that skips the HTTP handshake (no Servo backend needed)
    but points at the real local classifier.
    """
    original_post_init = Servo.__post_init__

    def _bypass_post_init(self: Servo) -> None:
        self._classifier_url = _CLASSIFIER_URL
        self._default_conversation = None
        self._embedding_fn_cache = None
        import threading
        self._db_lock = threading.Lock()
        self._cached_config = CachedConfig(
            key_id="test-key-id",
            user_id="test-user",
            model="test-model",
            tags=[],
            tiers={"simple": "gemma-3-27b-it", "complex": "claude-opus-4-5"},
            routing_config=RoutingConfig(
                default_category_id="simple",
                categories=_SAMPLE_CATEGORIES,
            ),
        )

    Servo.__post_init__ = _bypass_post_init
    try:
        client = Servo(api_key="sk_integration_test", timeout_s=120.0)
    finally:
        Servo.__post_init__ = original_post_init

    return client


def _make_mock_client(extra_categories: list[RoutingCategory] | None = None) -> Servo:
    """Build a Servo client with routing config but no HTTP or classifier — for unit tests."""
    categories = _SAMPLE_CATEGORIES + (extra_categories or [])
    original_post_init = Servo.__post_init__

    def _bypass_post_init(self: Servo) -> None:
        self._classifier_url = "http://localhost:8080"
        self._default_conversation = None
        self._embedding_fn_cache = None
        import threading
        self._db_lock = threading.Lock()
        self._cached_config = CachedConfig(
            key_id="test-key-id",
            user_id="test-user",
            model="test-model",
            tags=[],
            tiers={},
            routing_config=RoutingConfig(
                default_category_id="simple",
                categories=categories,
            ),
        )

    Servo.__post_init__ = _bypass_post_init
    try:
        client = Servo(api_key="sk_unit_test", timeout_s=30.0)
    finally:
        Servo.__post_init__ = original_post_init

    return client


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client() -> Servo:
    if not _classifier_reachable():
        pytest.skip(f"Classifier not reachable at {_CLASSIFIER_URL}")
    return _make_integration_client()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

PROMPTS = [
    (
        "simple",
        "What is the capital of France?",
    ),
    (
        "multi-step",
        "Build a REST API with authentication, a PostgreSQL database, and deploy it to AWS with auto-scaling.",
    ),
    (
        "mixed",
        "Summarise this article, translate it into Spanish, then store the translation in a SQLite database.",
    ),
]


@pytest.mark.parametrize("label,prompt", PROMPTS, ids=[p[0] for p in PROMPTS])
def test_decompose_and_classify_pipeline(client: Servo, label: str, prompt: str) -> None:
    """
    Runs the full decompose → classify LCEL pipeline against the live classifier
    and prints each subtask with its complexity assignment.
    """
    print(f"\n{'='*60}")
    print(f"Prompt ({label}): {prompt}")
    print("=" * 60)

    result = client.decompose_and_classify(prompt)

    assert isinstance(result, ClassifiedDecompositionResult)
    assert len(result.subtasks) > 0, "Pipeline returned no subtasks"

    valid_ids = {c.id for c in _SAMPLE_CATEGORIES}

    for subtask in result.subtasks:
        assert isinstance(subtask, ClassifiedSubtask)
        assert subtask.id, "Subtask missing id"
        assert subtask.text, "Subtask missing text"
        assert subtask.complexity_id in valid_ids, (
            f"Unknown complexity_id '{subtask.complexity_id}' — "
            f"expected one of {valid_ids}"
        )
        assert subtask.complexity_reasoning, "Subtask missing complexity_reasoning"

        deps = f" (depends on: {subtask.depends_on})" if subtask.depends_on else ""
        print(
            f"  [{subtask.complexity_id.upper()}] {subtask.id}: {subtask.text}{deps}\n"
            f"         reason: {subtask.complexity_reasoning}"
        )

    print(f"\nTotal subtasks: {len(result.subtasks)}")


def test_decompose_and_classify_subtask_count_scales_with_complexity(client: Servo) -> None:
    """
    A complex prompt should produce more subtasks than a trivial one.
    """
    simple = client.decompose_and_classify("Add 2 + 2.")
    complex_ = client.decompose_and_classify(
        "Design and implement a microservices architecture with service discovery, "
        "an API gateway, distributed tracing, CI/CD pipelines, and Kubernetes deployment manifests."
    )

    print(f"\nSimple prompt subtask count  : {len(simple.subtasks)}")
    print(f"Complex prompt subtask count : {len(complex_.subtasks)}")

    assert len(complex_.subtasks) >= len(simple.subtasks), (
        "Expected complex prompt to yield at least as many subtasks as a trivial one"
    )


def test_decompose_and_classify_dependency_graph_is_valid(client: Servo) -> None:
    """
    All dependsOn IDs must reference subtasks that exist in the result.
    """
    result = client.decompose_and_classify(
        "Write unit tests for a Python module, fix any bugs found, then open a pull request."
    )

    subtask_ids = {s.id for s in result.subtasks}
    for subtask in result.subtasks:
        for dep_id in subtask.depends_on:
            assert dep_id in subtask_ids, (
                f"Subtask '{subtask.id}' has a dependsOn reference '{dep_id}' "
                f"that does not exist in the result"
            )

    print(f"\nSubtasks and dependencies:")
    for s in result.subtasks:
        print(f"  {s.id} [{s.complexity_id}]: {s.text}")
        if s.depends_on:
            print(f"       depends on: {s.depends_on}")


# ---------------------------------------------------------------------------
# Stage 5: route_and_execute — unit tests (no live LLM or classifier required)
# ---------------------------------------------------------------------------

def _fake_llm(response: str) -> MagicMock:
    """Return a MagicMock that behaves like a LangChain chat model."""
    llm = MagicMock()
    msg = MagicMock()
    msg.content = response
    llm.invoke.return_value = msg
    return llm


def _make_context_db() -> ContextDB:
    """Construct a ContextDB backed by a real ephemeral ChromaDB (no embeddings needed for tests)."""
    from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
    return ContextDB(DefaultEmbeddingFunction())


def test_route_and_execute_simple_prompt() -> None:
    """
    E2E simple prompt: single subtask with no dependencies.
    final_response should equal the single subtask response directly.
    Verifies: routing to 'simple' tier, correct SubtaskExecutionResult fields.
    """
    client = _make_mock_client()

    subtask = ContextualizedSubtask(
        id="task-1",
        text="What is the capital of France?",
        depends_on=[],
        complexity_id="simple",
        complexity_reasoning="Factual lookup, no reasoning required",
        context=[],
    )
    contextualized = ContextualizedDecompositionResult(subtasks=[subtask])
    db = _make_context_db()
    db.add("task-1", subtask.text)

    with patch.object(client, "_build_llm", return_value=_fake_llm("Paris.")):
        result = client.route_and_execute(contextualized, db)

    assert isinstance(result, ExecutionResult)
    assert len(result.subtask_results) == 1

    r = result.subtask_results[0]
    assert r.subtask_id == "task-1"
    assert r.complexity_id == "simple"
    assert r.model == "gemma-3-27b-it"
    assert r.response == "Paris."
    assert r.used_default_category is False
    assert result.final_response == "Paris."


def test_route_and_execute_complex_prompt_dag() -> None:
    """
    E2E complex prompt: multi-step DAG with dependencies.
    task-A (no deps) → task-B (depends on A) → task-C (depends on B).

    Verifies:
    - Wave execution order: A before B before C
    - Each subtask gets its upstream context injected
    - final_response is only the terminal node (task-C)
    - task-A and task-B classified as different tiers
    """
    client = _make_mock_client()

    subtasks = [
        ContextualizedSubtask(
            id="task-A",
            text="Summarise the article.",
            depends_on=[],
            complexity_id="simple",
            complexity_reasoning="Straightforward summarisation",
            context=[],
        ),
        ContextualizedSubtask(
            id="task-B",
            text="Translate the summary into Spanish.",
            depends_on=["task-A"],
            complexity_id="medium",
            complexity_reasoning="Requires language translation",
            context=[],
        ),
        ContextualizedSubtask(
            id="task-C",
            text="Store the translation in a database.",
            depends_on=["task-B"],
            complexity_id="complex",
            complexity_reasoning="Requires code generation and DB interaction",
            context=[],
        ),
    ]
    contextualized = ContextualizedDecompositionResult(subtasks=subtasks)
    db = _make_context_db()
    for s in subtasks:
        db.add(s.id, s.text)

    execution_order: list[str] = []

    def _fake_llm_ordered(category):
        sid_response = {
            "task-A": "Article summary.",
            "task-B": "Resumen del artículo.",
            "task-C": "Translation stored successfully.",
        }
        llm = MagicMock()
        def invoke(messages):
            # Identify which subtask by inspecting the human message content
            human_text = messages[-1].content
            matching = next(
                (sid for sid, s in {s.id: s for s in subtasks}.items() if s.text in human_text),
                None,
            )
            if matching:
                execution_order.append(matching)
            msg = MagicMock()
            msg.content = sid_response.get(matching, "done")
            return msg
        llm.invoke.side_effect = invoke
        return llm

    with patch.object(client, "_build_llm", side_effect=_fake_llm_ordered):
        result = client.route_and_execute(contextualized, db)

    assert len(result.subtask_results) == 3
    # Wave ordering: A must complete before B, B before C
    assert execution_order.index("task-A") < execution_order.index("task-B")
    assert execution_order.index("task-B") < execution_order.index("task-C")

    by_id = {r.subtask_id: r for r in result.subtask_results}
    assert by_id["task-A"].response == "Article summary."
    assert by_id["task-B"].response == "Resumen del artículo."
    assert by_id["task-C"].response == "Translation stored successfully."

    # Only task-C is a terminal node (nothing depends on it)
    assert result.final_response == "Translation stored successfully."

    # Dependency chain: task-A and task-B are NOT terminals
    dependency_ids = set()
    for r in result.subtask_results:
        dependency_ids.update(r.depends_on)
    assert "task-A" in dependency_ids
    assert "task-B" in dependency_ids
    assert "task-C" not in dependency_ids


def test_route_and_execute_fallback_to_default_category() -> None:
    """
    When a subtask has an unknown complexity_id, the default category should be used
    and used_default_category should be True.
    """
    client = _make_mock_client()

    subtask = ContextualizedSubtask(
        id="task-x",
        text="Do something obscure.",
        depends_on=[],
        complexity_id="nonexistent_tier",
        complexity_reasoning="Unknown tier",
        context=[],
    )
    contextualized = ContextualizedDecompositionResult(subtasks=[subtask])
    db = _make_context_db()
    db.add("task-x", subtask.text)

    with patch.object(client, "_build_llm", return_value=_fake_llm("done")):
        result = client.route_and_execute(contextualized, db)

    r = result.subtask_results[0]
    assert r.used_default_category is True
    assert r.complexity_id == "simple"   # default_category_id in mock config


def test_route_and_execute_parallel_wave() -> None:
    """
    Four independent subtasks (Wave 0) should all execute and write to ContextDB.
    Concurrent writes are tested via a brief sleep in the mock LLM.
    """
    client = _make_mock_client()

    subtasks = [
        ContextualizedSubtask(
            id=f"task-{i}",
            text=f"Task {i}",
            depends_on=[],
            complexity_id="simple",
            complexity_reasoning="",
            context=[],
        )
        for i in range(4)
    ]
    contextualized = ContextualizedDecompositionResult(subtasks=subtasks)
    db = _make_context_db()
    for s in subtasks:
        db.add(s.id, s.text)

    def _slow_llm(category):
        llm = MagicMock()
        def invoke(messages):
            time.sleep(0.05)  # stress concurrent writes
            msg = MagicMock()
            msg.content = f"response for {messages[-1].content}"
            return msg
        llm.invoke.side_effect = invoke
        return llm

    with patch.object(client, "_build_llm", side_effect=_slow_llm):
        result = client.route_and_execute(contextualized, db, max_workers=4)

    assert len(result.subtask_results) == 4
    result_ids = {r.subtask_id for r in result.subtask_results}
    assert result_ids == {f"task-{i}" for i in range(4)}

    # All four should be terminal nodes (no dependencies)
    assert len(result.final_response.split("\n\n")) == 4


def test_route_and_execute_cycle_detection() -> None:
    """A cyclic dependency graph should raise ServoRoutingError."""
    client = _make_mock_client()

    subtasks = [
        ContextualizedSubtask(
            id="task-A", text="A", depends_on=["task-B"],
            complexity_id="simple", complexity_reasoning="", context=[],
        ),
        ContextualizedSubtask(
            id="task-B", text="B", depends_on=["task-A"],
            complexity_id="simple", complexity_reasoning="", context=[],
        ),
    ]
    contextualized = ContextualizedDecompositionResult(subtasks=subtasks)
    db = _make_context_db()

    with pytest.raises(ServoRoutingError, match="cycle"):
        client.route_and_execute(contextualized, db)


def test_context_db_cleared_after_full_pipeline() -> None:
    """
    decompose_classify_embed_and_execute should call db.close() even on success.
    Verified by patching decompose_classify_and_embed and route_and_execute.
    """
    client = _make_mock_client()

    mock_db = MagicMock(spec=ContextDB)
    mock_contextualized = ContextualizedDecompositionResult(subtasks=[])
    mock_result = ExecutionResult(subtask_results=[])

    with (
        patch.object(client, "decompose_classify_and_embed", return_value=(mock_contextualized, mock_db)),
        patch.object(client, "route_and_execute", return_value=mock_result),
    ):
        result = client.decompose_classify_embed_and_execute("test prompt")

    mock_db.close.assert_called_once()
    assert result is mock_result


# ---------------------------------------------------------------------------
# Stage 5: E2E live tests (classifier + real LLM)
# Skipped unless both the classifier is reachable AND GOOGLE_AI_STUDIO_API_KEY is set.
# Run with: pytest tests/test_integration.py -k "e2e_live" -v -s
# ---------------------------------------------------------------------------

_needs_live_execution = pytest.mark.skipif(
    not os.environ.get("GOOGLE_AI_STUDIO_API_KEY"),
    reason="GOOGLE_AI_STUDIO_API_KEY not set — skipping live E2E execution tests",
)


def _make_live_client() -> Servo:
    """
    Integration client with provider_api_keys wired from the environment.
    Still bypasses the Servo backend handshake — only the classifier and LLM are live.
    """
    client = _make_integration_client()
    client.provider_api_keys["google"] = os.environ["GOOGLE_AI_STUDIO_API_KEY"]
    return client


@_needs_live_execution
def test_e2e_live_simple_prompt() -> None:
    """
    Live E2E — simple prompt.

    A single-fact question should decompose into exactly one subtask, be routed
    to the 'simple' tier (gemma-3-27b-it), and return a short non-empty answer.
    """
    if not _classifier_reachable():
        pytest.skip(f"Classifier not reachable at {_CLASSIFIER_URL}")

    client = _make_live_client()
    prompt = "What is the capital of France?"

    result = client.decompose_classify_embed_and_execute(prompt)

    print(f"\n{'='*60}")
    print(f"Prompt: {prompt}")
    print(f"Subtasks: {len(result.subtask_results)}")
    for r in result.subtask_results:
        print(f"  [{r.complexity_id}] {r.subtask_id}: {r.subtask_text}")
        print(f"         model: {r.model}")
        print(f"         response: {r.response[:200]}")
    print(f"\nfinal_response:\n{result.final_response}")

    assert len(result.subtask_results) >= 1, "Expected at least one subtask"
    assert result.final_response.strip() != "", "final_response should not be empty"

    # Simple factual prompt should be routed to the cheap tier
    for r in result.subtask_results:
        assert r.complexity_id in {"simple", "medium"}, (
            f"Simple prompt subtask '{r.subtask_id}' was unexpectedly routed to '{r.complexity_id}'"
        )

    # The word "Paris" should appear somewhere in the response
    assert "paris" in result.final_response.lower(), (
        f"Expected 'Paris' in response, got: {result.final_response!r}"
    )


@_needs_live_execution
def test_e2e_live_complex_prompt() -> None:
    """
    Live E2E — complex multi-step prompt.

    A prompt with explicit sequential steps should decompose into 2+ subtasks
    with dependency relationships. The final_response should be the terminal
    node(s) only, and should contain output relevant to the last step.
    """
    if not _classifier_reachable():
        pytest.skip(f"Classifier not reachable at {_CLASSIFIER_URL}")

    client = _make_live_client()
    prompt = (
        "Summarise the following text in one sentence, "
        "then translate that summary into French: "
        "'The Eiffel Tower was built in 1889 as the entrance arch for the 1889 World's Fair.'"
    )

    result = client.decompose_classify_embed_and_execute(prompt)

    print(f"\n{'='*60}")
    print(f"Prompt: {prompt}")
    print(f"Subtasks: {len(result.subtask_results)}")
    for r in result.subtask_results:
        deps = f" (depends on: {r.depends_on})" if r.depends_on else ""
        print(f"  [{r.complexity_id}] {r.subtask_id}: {r.subtask_text}{deps}")
        print(f"         model: {r.model}")
        print(f"         response: {r.response[:300]}")
    print(f"\nfinal_response:\n{result.final_response}")

    assert len(result.subtask_results) >= 2, (
        "Expected 2+ subtasks for a multi-step prompt, "
        f"got {len(result.subtask_results)}"
    )
    assert result.final_response.strip() != "", "final_response should not be empty"

    # At least one subtask should have a dependency
    has_deps = any(r.depends_on for r in result.subtask_results)
    assert has_deps, "Expected at least one subtask to declare a dependency"

    # The final_response should only contain terminal node(s) — not all subtask responses
    all_responses = [r.response for r in result.subtask_results]
    # Terminal = not referenced in any depends_on; for a linear chain the last one is terminal
    dependency_ids = set()
    for r in result.subtask_results:
        dependency_ids.update(r.depends_on)
    terminal_responses = [r.response for r in result.subtask_results if r.subtask_id not in dependency_ids]
    assert result.final_response == "\n\n".join(terminal_responses)

    # The translation step should produce output that looks French (contains accented chars
    # or common French words) — loose check since exact wording varies
    final_lower = result.final_response.lower()
    french_indicators = ["la ", "le ", "les ", "de ", "du ", "en ", "été", "tour", "eiffel"]
    assert any(ind in final_lower for ind in french_indicators), (
        f"final_response doesn't look like a French translation: {result.final_response!r}"
    )
