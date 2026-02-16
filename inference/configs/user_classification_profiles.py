"""Hardcoded placeholder for per-user classification categories.

This module exists as an MVP bridge until category profiles are persisted in DB.
"""

from typing import Any
from pydantic import BaseModel, Field


class ClassificationCategory(BaseModel):
    """A routeable classification category for one user."""

    id: str = Field(description="Stable category id")
    name: str = Field(description="Display name used by clients")
    description: str = Field(description="Classifier guidance for this category")
    provider: str = Field(description="Provider identifier, e.g. google_ai_studio")
    endpoint: str = Field(description="Provider endpoint URL")
    model_id: str = Field(description="Exact provider model id")
    request_defaults: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional provider request defaults such as temperature"
    )


class UserClassificationProfile(BaseModel):
    """Per-user category profile."""

    user_id: str
    categories: list[ClassificationCategory]
    default_category_id: str


GOOGLE_AI_STUDIO_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/openai/"
GOOGLE_AI_STUDIO_PROVIDER = "google_ai_studio"

DEFAULT_PROFILE = UserClassificationProfile(
    user_id="default_user",
    default_category_id="simple",
    categories=[
        ClassificationCategory(
            id="simple",
            name="Simple",
            description=(
                "Use for direct, bounded tasks: factual Q&A, concise explanations, "
                "and routine coding work (for example implementing a single Python function, "
                "small bug fixes, or straightforward refactors). Prefer this category whenever "
                "the request can be fully handled without deep multi-step analysis."
            ),
            provider=GOOGLE_AI_STUDIO_PROVIDER,
            endpoint=GOOGLE_AI_STUDIO_ENDPOINT,
            model_id="gemma-3-27b-it",
            request_defaults={"temperature": 0.2},
        ),
        ClassificationCategory(
            id="complex",
            name="Complex",
            description=(
                "Use only when the task genuinely requires deeper reasoning: broad system design, "
                "non-trivial architecture or migration plans, advanced debugging across multiple "
                "interacting components, or nuanced tradeoff analysis. Do not use for routine "
                "single-file or single-function coding tasks."
            ),
            provider=GOOGLE_AI_STUDIO_PROVIDER,
            endpoint=GOOGLE_AI_STUDIO_ENDPOINT,
            model_id="gemini-2.5-flash",
            request_defaults={"temperature": 0.2},
        ),
    ],
)

# Placeholder users for MVP validation. Replace with DB-backed profiles later.
USER_CLASSIFICATION_PROFILES: dict[str, UserClassificationProfile] = {
    DEFAULT_PROFILE.user_id: DEFAULT_PROFILE,
    "demo_user": DEFAULT_PROFILE.model_copy(update={"user_id": "demo_user"}),
}


def get_user_profile(user_id: str) -> UserClassificationProfile:
    """Resolve profile for user_id; raises ValueError when unknown."""
    if user_id not in USER_CLASSIFICATION_PROFILES:
        raise ValueError(f"Unknown user_id '{user_id}'. No classification profile configured.")
    return USER_CLASSIFICATION_PROFILES[user_id]


def list_user_categories(user_id: str) -> list[ClassificationCategory]:
    """List categories configured for a user."""
    return get_user_profile(user_id).categories


def list_user_ids() -> list[str]:
    """List hardcoded users available in the placeholder profile store."""
    return sorted(USER_CLASSIFICATION_PROFILES.keys())
