"""Prompt classification service using Outlines with a local OpenAI-compatible backend."""

import os
import outlines
from openai import OpenAI
from enum import Enum
from pydantic import BaseModel, Field, create_model
from typing import Optional, Type

from ..configs.user_classification_profiles import UserClassificationProfile
from ..models.classification import ClassificationResult


class PromptClassifier:
    """Classifier service for determining prompt category using Outlines."""

    def __init__(self, config: Optional[dict] = None):
        """
        Initialize the classifier.

        Args:
            config: Optional configuration dict. If not provided,
                    loads from environment variables.
        """
        self.endpoint = os.getenv(
            "CLASSIFIER_ENDPOINT",
            config.get("endpoint", "http://localhost:8080/v1") if config else "http://localhost:8080/v1"
        )
        self.model_name = os.getenv(
            "CLASSIFIER_MODEL",
            config.get("model", "qwen3-14b") if config else "qwen3-14b"
        )
        self.temperature = float(os.getenv(
            "CLASSIFIER_TEMPERATURE",
            config.get("temperature", 0.1) if config else 0.1
        ))

        # Initialize OpenAI client and Outlines wrapper
        # outlines.from_openai() wraps the client to enforce structured output
        self.client = OpenAI(base_url=self.endpoint, api_key="not-needed")
        self.model = outlines.from_openai(self.client, self.model_name)

    def _build_category_schema(self, profile: UserClassificationProfile) -> Type[BaseModel]:
        """Build a dynamic schema constrained to the user's configured category ids."""
        enum_members = {
            category.id.upper().replace("-", "_"): category.id
            for category in profile.categories
        }
        category_enum = Enum("AllowedCategory", enum_members, type=str)

        return create_model(
            "CategorySelection",
            category_id=(category_enum, Field(description="One of the allowed category ids")),
            reasoning=(str, Field(description="Why this category was selected")),
            confidence=(float, Field(ge=0.0, le=1.0)),
        )

    def _build_prompt(self, prompt: str, profile: UserClassificationProfile) -> str:
        """Build classifier prompt constrained to this user's categories."""
        category_lines = [
            f"- id={category.id}, name={category.name}, description={category.description}"
            for category in profile.categories
        ]
        categories_blob = "\n".join(category_lines)
        return (
            "Classify the following user prompt into exactly one configured category.\n"
            "Only choose from the allowed category ids listed below.\n\n"
            "Routing policy:\n"
            "- Select the lowest-complexity category that can fully complete the request.\n"
            "- If both a simpler and a more complex category could work, choose the simpler one.\n"
            "- Choose a more complex category only when the simpler one is clearly insufficient.\n\n"
            f"Allowed categories:\n{categories_blob}\n\n"
            f"User prompt:\n{prompt}\n"
        )

    def _fallback_category(self, profile: UserClassificationProfile) -> tuple[str, str]:
        """Return deterministic fallback category (default id if present, otherwise first category)."""
        by_id = {category.id: category for category in profile.categories}
        fallback = by_id.get(profile.default_category_id, profile.categories[0])
        return fallback.id, fallback.name

    @staticmethod
    def _to_category_id(value: object) -> str:
        """
        Normalize model output category identifier to a plain category id string.

        Handles Enum instances from dynamic schema as well as raw strings.
        """
        if hasattr(value, "value"):
            return str(value.value)
        return str(value)

    def classify(self, prompt: str, profile: UserClassificationProfile) -> ClassificationResult:
        """
        Classify a prompt into one of the user's configured categories.

        Args:
            prompt: The user prompt to classify.
            profile: User-specific classification profile.

        Returns:
            ClassificationResult with selected category and metadata.
        """
        schema_model = self._build_category_schema(profile)
        classification_prompt = self._build_prompt(prompt, profile)
        result = self.model(classification_prompt, schema_model)

        # If result is a string (JSON), parse it into the Pydantic model
        if isinstance(result, str):
            parsed = schema_model.model_validate_json(result)
        else:
            parsed = result

        selected_category_id = self._to_category_id(parsed.category_id)
        categories_by_id = {category.id: category for category in profile.categories}
        selected_category = categories_by_id.get(selected_category_id)
        if selected_category is None:
            fallback_id, fallback_name = self._fallback_category(profile)
            return ClassificationResult(
                category_id=fallback_id,
                category_name=fallback_name,
                reasoning="Model returned an invalid category; fallback applied.",
                confidence=0.3,
            )

        return ClassificationResult(
            category_id=selected_category.id,
            category_name=selected_category.name,
            reasoning=parsed.reasoning,
            confidence=parsed.confidence,
        )

    def quick_classify(self, prompt: str, profile: UserClassificationProfile) -> ClassificationResult:
        """
        Perform a quick heuristic classification without calling the model.
        Useful for obvious cases or when the model is unavailable.

        Args:
            prompt: The user prompt to classify.
            profile: User-specific classification profile.

        Returns:
            ClassificationResult based on heuristics.
        """
        prompt_lower = prompt.lower().strip()
        token_estimate = len(prompt) // 4  # Rough token estimate

        categories_by_id = {category.id: category for category in profile.categories}
        simple_category = next(
            (category for category in profile.categories if "simple" in f"{category.id} {category.name}".lower()),
            categories_by_id.get(profile.default_category_id, profile.categories[0]),
        )
        complex_category = next(
            (category for category in profile.categories if "complex" in f"{category.id} {category.name}".lower()),
            profile.categories[-1],
        )

        complex_keywords = [
            "analyze", "compare", "explain why", "implications",
            "pros and cons", "evaluate", "critique", "in-depth",
            "step by step", "design", "architecture", "debug",
            "optimize", "algorithm", "prove", "tradeoff"
        ]
        if token_estimate > 2000 or any(kw in prompt_lower for kw in complex_keywords):
            return ClassificationResult(
                category_id=complex_category.id,
                category_name=complex_category.name,
                reasoning="Quick heuristic classification marked as complex.",
                confidence=0.7,
            )

        return ClassificationResult(
            category_id=simple_category.id,
            category_name=simple_category.name,
            reasoning="Quick heuristic classification marked as simple.",
            confidence=0.7,
        )
