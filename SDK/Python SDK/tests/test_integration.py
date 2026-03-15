"""
Integration tests for the decompose_and_classify pipeline.

These tests call the actual classifier running at localhost:8080 (or the URL set
in CLASSIFIER_ENDPOINT).  They are skipped automatically when the classifier is
not reachable, so they are safe to run in CI without a local model server.

Run them explicitly:
    pytest tests/test_integration.py -v -s
"""
from __future__ import annotations

import os
import urllib.request
import urllib.error
from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest

from servo_sdk import (
    Servo,
    ClassifiedDecompositionResult,
    ClassifiedSubtask,
    RoutingCategory,
)
from servo_sdk.types import CachedConfig, RoutingConfig


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
