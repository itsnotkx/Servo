"""
E2E integration tests for the full Stage 5 pipeline (decompose → classify → embed → route → execute).

Uses a 2-category routing config (Simple→Gemma, Complex→GeminiFlashLite) and breaks out
each pipeline stage explicitly so the flow is visible in test output.

Run with:
    cd "SDK/Python SDK"
    GOOGLE_AI_STUDIO_API_KEY=<key> pytest tests/test_e2e.py -v -s

Skipped automatically when:
  - GOOGLE_AI_STUDIO_API_KEY is not set
  - Classifier is not reachable at CLASSIFIER_ENDPOINT (default: http://localhost:8080)
"""
from __future__ import annotations

import os
import threading
import urllib.error
import urllib.request

import pytest

from servo_sdk import (
    Servo,
    RoutingCategory,
)
from servo_sdk.client import ContextDB
from servo_sdk.types import CachedConfig, RoutingConfig


# ---------------------------------------------------------------------------
# Routing config for E2E tests (2 categories)
# ---------------------------------------------------------------------------

_E2E_CATEGORIES = [
    RoutingCategory(
        id="simple",
        name="Simple",
        description="Straightforward, no reasoning",
        model="gemma-3-27b-it",
    ),
    RoutingCategory(
        id="complex",
        name="Complex",
        description="Multi-step reasoning required",
        model="gemini-3.1-flash-lite-preview",
    ),
]
_E2E_CONFIG = RoutingConfig(default_category_id="simple", categories=_E2E_CATEGORIES)

_CLASSIFIER_URL: str = os.environ.get("CLASSIFIER_ENDPOINT", "http://localhost:8080")

_E2E_MODELS = {"gemma-3-27b-it", "gemini-3.1-flash-lite-preview"}

# ---------------------------------------------------------------------------
# Skip markers
# ---------------------------------------------------------------------------

_needs_live = pytest.mark.skipif(
    not os.environ.get("GOOGLE_AI_STUDIO_API_KEY"),
    reason="GOOGLE_AI_STUDIO_API_KEY not set — skipping live E2E tests",
)


def _classifier_reachable() -> bool:
    """Return True if the classifier health endpoint responds."""
    try:
        with urllib.request.urlopen(
            _CLASSIFIER_URL.rstrip("/") + "/health", timeout=2
        ):
            return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Client factory
# ---------------------------------------------------------------------------

def _make_e2e_client() -> Servo:
    """
    Build a Servo client that bypasses the HTTP backend handshake but uses the
    real classifier and the 2-category E2E routing config.
    """
    original_post_init = Servo.__post_init__

    def _bypass_post_init(self: Servo) -> None:
        self._classifier_url = _CLASSIFIER_URL
        self._default_conversation = None
        self._embedding_fn_cache = None
        self._db_lock = threading.Lock()
        self._cached_config = CachedConfig(
            key_id="e2e-test-key-id",
            user_id="e2e-test-user",
            model="test-model",
            tags=[],
            tiers={c.id: c.model for c in _E2E_CATEGORIES},
            routing_config=_E2E_CONFIG,
        )

    Servo.__post_init__ = _bypass_post_init
    try:
        client = Servo(api_key="sk_e2e_test", timeout_s=120.0)
    finally:
        Servo.__post_init__ = original_post_init

    client.provider_api_keys["google"] = os.environ["GOOGLE_AI_STUDIO_API_KEY"]
    return client


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@_needs_live
def test_e2e_simple_prompt() -> None:
    """
    Live E2E — simple prompt.

    Verifies the full pipeline with a single-fact question that should classify
    as 'simple' and route to Gemma.  Each stage is called explicitly.
    """
    if not _classifier_reachable():
        pytest.skip(f"Classifier not reachable at {_CLASSIFIER_URL}")

    client = _make_e2e_client()
    prompt = "What is the boiling point of water in Celsius?"

    # Stage 1+2: decompose and classify
    classified = client.decompose_and_classify(prompt)
    print(f"\n{'='*60}")
    print(f"Prompt: {prompt}")
    print(f"Subtasks after decompose+classify ({len(classified.subtasks)}):")
    for st in classified.subtasks:
        print(f"  [{st.complexity_id}] {st.id}: {st.text}")

    # Stage 3: embed and contextualize
    contextualized, db = client.embed_and_contextualize(classified)
    try:
        # Assert first subtask is stored in the vector DB
        first_id = contextualized.subtasks[0].id
        stored = db.get_by_id(first_id)
        assert stored, f"Expected DB entry for subtask {first_id!r}, got empty result"

        # Stage 4+5: route and execute
        result = client.route_and_execute(contextualized, db)
    finally:
        db.close()

    # Print output for human review
    print(f"\nExecution results ({len(result.subtask_results)} subtask(s)):")
    for r in result.subtask_results:
        print(f"  [{r.complexity_id}] {r.subtask_id} → model={r.model}")
        print(f"    response: {r.response[:300]}")
    print(f"\nfinal_response:\n{result.final_response}")
    print("=" * 60)

    # Assertions
    assert len(result.subtask_results) >= 1
    for r in result.subtask_results:
        assert r.complexity_id in {"simple", "complex"}, (
            f"Unexpected complexity_id {r.complexity_id!r} for subtask {r.subtask_id!r}"
        )
        assert r.model in _E2E_MODELS, (
            f"Unexpected model {r.model!r} for subtask {r.subtask_id!r}"
        )
    assert result.final_response.strip() != "", "final_response must not be empty"
    assert "100" in result.final_response, (
        f"Expected '100' in response for boiling-point question, got: {result.final_response!r}"
    )


@_needs_live
def test_e2e_complex_prompt() -> None:
    """
    Live E2E — complex prompt.

    A two-step prompt (explain recursion + write factorial function) should
    produce 2+ subtasks with a dependency chain, routing at least one subtask
    to the 'complex' tier.  Each stage is called explicitly.
    """
    if not _classifier_reachable():
        pytest.skip(f"Classifier not reachable at {_CLASSIFIER_URL}")

    client = _make_e2e_client()
    prompt = (
        "Explain what recursion is in one sentence, then write a Python function "
        "that uses recursion to compute the factorial of a number."
    )

    # Stage 1+2: decompose and classify
    classified = client.decompose_and_classify(prompt)
    print(f"\n{'='*60}")
    print(f"Prompt: {prompt}")
    print(f"Subtasks after decompose+classify ({len(classified.subtasks)}):")
    for st in classified.subtasks:
        depends = f" (depends_on={st.depends_on})" if st.depends_on else ""
        print(f"  [{st.complexity_id}] {st.id}: {st.text}{depends}")

    # Stage 3: embed and contextualize
    contextualized, db = client.embed_and_contextualize(classified)
    try:
        # Assert every subtask is stored in the vector DB
        for st in contextualized.subtasks:
            stored = db.get_by_id(st.id)
            assert stored, f"Expected DB entry for subtask {st.id!r}, got empty result"

        # Stage 4+5: route and execute
        result = client.route_and_execute(contextualized, db)
    finally:
        db.close()

    # Print output for human review
    print(f"\nExecution results ({len(result.subtask_results)} subtask(s)):")
    for r in result.subtask_results:
        context_note = " [context injected]" if r.depends_on else ""
        print(f"  [{r.complexity_id}] {r.subtask_id} → model={r.model}{context_note}")
        print(f"    response: {r.response[:400]}")
    print(f"\nfinal_response:\n{result.final_response}")
    print("=" * 60)

    # Assertions
    assert len(result.subtask_results) >= 2, (
        f"Expected >= 2 subtasks for complex prompt, got {len(result.subtask_results)}"
    )

    # At least one subtask must have a dependency
    assert any(r.depends_on for r in result.subtask_results), (
        "Expected at least one subtask with a depends_on dependency"
    )

    for r in result.subtask_results:
        assert r.complexity_id in {"simple", "complex"}, (
            f"Unexpected complexity_id {r.complexity_id!r} for subtask {r.subtask_id!r}"
        )
        assert r.model in _E2E_MODELS, (
            f"Unexpected model {r.model!r} for subtask {r.subtask_id!r}"
        )

    # final_response should match the terminal-node join pattern
    dependency_ids: set[str] = set()
    for r in result.subtask_results:
        dependency_ids.update(r.depends_on)
    terminal_responses = [
        r.response for r in result.subtask_results if r.subtask_id not in dependency_ids
    ]
    assert result.final_response == "\n\n".join(terminal_responses)

    assert result.final_response.strip() != "", "final_response must not be empty"
    assert ("def " in result.final_response or "factorial" in result.final_response), (
        f"Expected code output (def/factorial) in final response, got: {result.final_response!r}"
    )
