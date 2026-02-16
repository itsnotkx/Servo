"""Category-based routing service."""

from typing import Optional

from ..configs.user_classification_profiles import (
    ClassificationCategory,
    UserClassificationProfile,
    get_user_profile,
)
from ..models.classification import ClassificationResult


class LLMRouter:
    """Router that maps classification categories to provider route metadata."""

    def __init__(self, config: Optional[dict] = None):
        """
        Initialize the router.

        Args:
            config: Optional configuration dictionary (currently unused).
        """
        self.config = config or {}
        self.simple_preference_confidence_threshold = float(
            self.config.get("simple_preference_confidence_threshold", 0.7)
        )

    @staticmethod
    def _is_simple_like(category: ClassificationCategory) -> bool:
        """Heuristic check for categories representing simpler routing tiers."""
        marker = f"{category.id} {category.name}".lower()
        return "simple" in marker

    @staticmethod
    def _is_complex_like(category: ClassificationCategory) -> bool:
        """Heuristic check for categories representing more complex routing tiers."""
        marker = f"{category.id} {category.name}".lower()
        return "complex" in marker

    def route(
        self,
        classification: ClassificationResult,
        profile: UserClassificationProfile,
    ) -> ClassificationCategory:
        """
        Resolve route category metadata from classification and user profile.

        Args:
            classification: Classification result from the classifier.
            profile: User-specific category profile.

        Returns:
            Fully resolved category metadata.
        """
        categories_by_id = {category.id: category for category in profile.categories}
        selected = categories_by_id.get(classification.category_id)
        if selected is None:
            raise ValueError(
                f"Invalid category '{classification.category_id}' for user '{profile.user_id}'."
            )

        default_category = categories_by_id.get(profile.default_category_id)
        if (
            default_category is not None
            and selected.id != default_category.id
            and self._is_simple_like(default_category)
            and self._is_complex_like(selected)
            and classification.confidence < self.simple_preference_confidence_threshold
        ):
            return default_category

        return selected

    def list_tiers(self, user_id: str) -> dict[str, str]:
        """Compatibility helper mapping category ids to model ids."""
        profile = get_user_profile(user_id)
        return {category.id: category.model_id for category in profile.categories}
