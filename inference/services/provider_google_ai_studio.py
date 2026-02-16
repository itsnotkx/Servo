"""Google AI Studio provider invocation service."""

import os
from openai import OpenAI

from ..configs.user_classification_profiles import ClassificationCategory


class GoogleAIStudioProvider:
    """Calls Google AI Studio via OpenAI-compatible API."""

    def __init__(self, api_key_env: str = "GOOGLE_AI_STUDIO_API_KEY"):
        self.api_key_env = api_key_env

    def generate(self, prompt: str, category: ClassificationCategory) -> str:
        """
        Generate completion for the prompt routed to the selected category model.

        Args:
            prompt: Original user prompt.
            category: Resolved category metadata.

        Returns:
            Text response from the provider model.
        """
        if category.provider != "google_ai_studio":
            raise ValueError(f"Unsupported provider '{category.provider}'.")

        api_key = os.getenv(self.api_key_env)
        if not api_key:
            raise ValueError(
                f"Missing required environment variable '{self.api_key_env}' for Google AI Studio."
            )

        client = OpenAI(base_url=category.endpoint, api_key=api_key)

        request_payload = dict(category.request_defaults)
        completion = client.chat.completions.create(
            model=category.model_id,
            messages=[{"role": "user", "content": prompt}],
            **request_payload,
        )
        return completion.choices[0].message.content or ""
