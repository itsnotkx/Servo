from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ._http import HTTPClient
from .context import Conversation
from .types import (
    ClassificationResult,
    ProcessingResult,
    RouteResponse,
    TiersResponse,
    CategoriesResponse,
)


@dataclass
class Servo:
    """
    Minimal Python client for the Servo backend.

    3-step flow:
      1) init client
      2) send prompt (optionally with context)
      3) receive typed response
    """

    api_key: str | None = None
    base_url: str = "http://localhost:8000"
    timeout_s: float = 30.0
    default_user_id: str = "default_user"

    def __post_init__(self) -> None:
        self._http = HTTPClient(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout_s=self.timeout_s,
        )
        self._default_conversation: Conversation | None = None

    def close(self) -> None:
        return

    def __enter__(self) -> "Servo":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def with_conversation(self, conversation: Conversation | None = None) -> Conversation:
        if conversation is None:
            conversation = Conversation()
        self._default_conversation = conversation
        return conversation

    def health(self) -> dict[str, Any]:
        return self._http.request_json("GET", "/health")

    def tiers(self, user_id: str | None = None) -> TiersResponse:
        user = user_id or self.default_user_id
        data = self._http.request_json("GET", f"/tiers?user_id={user}")
        return TiersResponse.from_dict(data)

    def categories(self, user_id: str | None = None) -> CategoriesResponse:
        user = user_id or self.default_user_id
        data = self._http.request_json("GET", f"/categories?user_id={user}")
        return CategoriesResponse.from_dict(data)

    def classify(
        self, prompt: str, user_id: str | None = None, *, use_quick: bool = False
    ) -> ClassificationResult:
        user = user_id or self.default_user_id
        data = self._http.request_json(
            "POST",
            "/classify",
            json_body={"user_id": user, "prompt": prompt, "use_quick": bool(use_quick)},
        )
        return ClassificationResult.from_dict(data)

    def route(
        self, classification: ClassificationResult, user_id: str | None = None
    ) -> RouteResponse:
        user = user_id or self.default_user_id
        data = self._http.request_json(
            "POST",
            "/route",
            json_body={"user_id": user, "classification": classification.to_dict()},
        )
        return RouteResponse.from_dict(data)

    def send(
        self,
        request_message: str,
        user_id: str | None = None,
        *,
        use_quick_classify: bool = False,
        conversation: Conversation | None = None,
    ) -> ProcessingResult:
        """
        Calls `POST /process` on the backend.

        Returns full processing result including classification, routing, and LLM response.
        """
        user = user_id or self.default_user_id
        
        if conversation is None:
            conversation = self._default_conversation

        prompt = (
            conversation.build_prompt(next_user_message=request_message)
            if conversation is not None
            else request_message
        )

        data = self._http.request_json(
            "POST",
            "/process",
            json_body={
                "user_id": user,
                "prompt": prompt,
                "use_quick_classify": bool(use_quick_classify),
            },
        )
        return ProcessingResult.from_dict(data)

