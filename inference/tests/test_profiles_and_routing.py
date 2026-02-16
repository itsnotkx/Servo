import pytest

from inference.configs.user_classification_profiles import get_user_profile
from inference.models.classification import ClassificationResult
from inference.services.router import LLMRouter


def test_get_user_profile_known_user():
    profile = get_user_profile("default_user")
    assert profile.user_id == "default_user"
    assert len(profile.categories) == 2


def test_get_user_profile_unknown_user_raises():
    with pytest.raises(ValueError):
        get_user_profile("missing-user")


def test_router_resolves_selected_category():
    router = LLMRouter()
    profile = get_user_profile("default_user")
    classification = ClassificationResult(
        category_id="simple",
        category_name="Simple",
        reasoning="factual question",
        confidence=0.9,
    )

    selected = router.route(classification, profile)
    assert selected.id == "simple"
    assert selected.model_id == "gemma-3-27b-it"


def test_router_rejects_invalid_category():
    router = LLMRouter()
    profile = get_user_profile("default_user")
    classification = ClassificationResult(
        category_id="not-allowed",
        category_name="Not Allowed",
        reasoning="invalid",
        confidence=0.1,
    )

    with pytest.raises(ValueError):
        router.route(classification, profile)


def test_router_prefers_default_simple_for_low_confidence_complex():
    router = LLMRouter()
    profile = get_user_profile("default_user")
    classification = ClassificationResult(
        category_id="complex",
        category_name="Complex",
        reasoning="could be either",
        confidence=0.45,
    )

    selected = router.route(classification, profile)
    assert selected.id == profile.default_category_id
    assert selected.id == "simple"


def test_router_keeps_complex_when_confidence_is_high():
    router = LLMRouter()
    profile = get_user_profile("default_user")
    classification = ClassificationResult(
        category_id="complex",
        category_name="Complex",
        reasoning="needs deep multi-step analysis",
        confidence=0.92,
    )

    selected = router.route(classification, profile)
    assert selected.id == "complex"
