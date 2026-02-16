from enum import Enum

from inference.configs.user_classification_profiles import get_user_profile
from inference.services.classifier import PromptClassifier


def test_to_category_id_converts_enum_to_plain_string():
    allowed = Enum("AllowedCategory", {"SIMPLE": "simple"}, type=str)
    assert PromptClassifier._to_category_id(allowed.SIMPLE) == "simple"


def test_to_category_id_keeps_plain_string():
    assert PromptClassifier._to_category_id("complex") == "complex"


def test_build_prompt_includes_simple_first_tiebreak_policy():
    classifier = PromptClassifier.__new__(PromptClassifier)
    profile = get_user_profile("default_user")

    prompt = classifier._build_prompt("Implement a Python add function", profile)

    assert "Select the lowest-complexity category" in prompt
    assert "choose the simpler one" in prompt
