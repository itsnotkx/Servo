"""Simple tier-based routing service."""

import os
from typing import Dict, Optional

from ..models.classification import ClassificationResult, ComplexityLevel


class LLMRouter:
    """Simple tier-based router that maps complexity levels to models."""

    # Default tier-to-model mapping (can be overridden by env vars)
    DEFAULT_TIER_MODELS: Dict[ComplexityLevel, str] = {
        ComplexityLevel.SIMPLE: "qwen-0.5b",
        ComplexityLevel.THINKING: "qwen-7b",
        ComplexityLevel.COMPLEX: "qwen-14b",
    }

    # Environment variable names for each tier
    ENV_VAR_MAPPING: Dict[ComplexityLevel, str] = {
        ComplexityLevel.SIMPLE: "TIER_SIMPLE_MODEL",
        ComplexityLevel.THINKING: "TIER_THINKING_MODEL",
        ComplexityLevel.COMPLEX: "TIER_COMPLEX_MODEL",
    }

    def __init__(self, config: Optional[dict] = None):
        """
        Initialize the router.

        Args:
            config: Optional configuration dict with tier overrides.
        """
        self.config = config or {}
        self.tier_models = self._load_tier_models()

    def _load_tier_models(self) -> Dict[ComplexityLevel, str]:
        """
        Load tier models from environment variables, falling back to defaults.

        Returns:
            Dictionary mapping ComplexityLevel to model name.
        """
        tier_models = {}

        for level in ComplexityLevel:
            env_var = self.ENV_VAR_MAPPING.get(level)
            default = self.DEFAULT_TIER_MODELS.get(level, "qwen-7b")

            # Priority: env var > config > default
            if env_var and os.getenv(env_var):
                tier_models[level] = os.getenv(env_var)
            elif level.value in self.config:
                tier_models[level] = self.config[level.value]
            else:
                tier_models[level] = default

        return tier_models

    def route(self, classification: ClassificationResult) -> str:
        """
        Route to appropriate model based on classification.

        Args:
            classification: The classification result from the classifier.

        Returns:
            Model name to use for this prompt.
        """
        # Handle string complexity (when serialized/deserialized)
        complexity = classification.complexity
        if isinstance(complexity, str):
            complexity = ComplexityLevel(complexity)

        return self.tier_models.get(
            complexity,
            self.tier_models[ComplexityLevel.THINKING]  # Fallback to thinking
        )

    def get_model_for_tier(self, tier: str) -> str:
        """
        Get the model for a specific tier by name.

        Args:
            tier: Tier name (e.g., 'simple', 'complex').

        Returns:
            Model name for the tier.
        """
        try:
            level = ComplexityLevel(tier)
            return self.tier_models.get(level, self.tier_models[ComplexityLevel.THINKING])
        except ValueError:
            return self.tier_models[ComplexityLevel.THINKING]

    def list_tiers(self) -> Dict[str, str]:
        """
        List all configured tiers and their models.

        Returns:
            Dictionary of tier names to model names.
        """
        return {level.value: model for level, model in self.tier_models.items()}

    def update_tier_model(self, tier: str, model: str) -> None:
        """
        Dynamically update a tier's model at runtime.

        Args:
            tier: Tier name to update.
            model: New model name.
        """
        try:
            level = ComplexityLevel(tier)
            self.tier_models[level] = model
        except ValueError:
            raise ValueError(f"Invalid tier name: {tier}")
