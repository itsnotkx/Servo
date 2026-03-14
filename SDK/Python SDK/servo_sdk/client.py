from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from ._http import HTTPClient
from .context import Conversation
from .errors import ServoAPIError, ServoAuthenticationError, ServoDecompositionError
from .types import (
    CachedConfig,
    ClassificationResult,
    ProcessingResult,
    RouteResponse,
    RoutingConfig,
    TiersResponse,
    CategoriesResponse,
    Subtask,
    DecompositionResult,
)

_SERVO_ENDPOINT = "https://servo.example.com"  # TODO: set to real prod URL
_CLASSIFIER_DEFAULT = "http://localhost:8080"

_DECOMPOSE_SYSTEM_PROMPT = (
    "You are a task decomposition assistant. "
    "Given a user prompt, break it into atomic, non-overlapping subtasks. "
    "Use 'dependsOn' to express task dependencies by referencing other subtask IDs."
)


@dataclass
class Servo:
    """
    Minimal Python client for the Servo backend.

    Usage:
        client = Servo("sk_live_...")
        result = client.send("Hello!")
    """

    api_key: str
    timeout_s: float = 30.0
    classifier_url: str | None = None

    def __post_init__(self) -> None:
        endpoint = os.environ.get("SERVO_ENDPOINT", _SERVO_ENDPOINT)
        self._http = HTTPClient(
            base_url=endpoint,
            api_key=self.api_key,
            timeout_s=self.timeout_s,
        )
        if self.classifier_url is None:
            self._classifier_url: str = os.environ.get("CLASSIFIER_ENDPOINT", _CLASSIFIER_DEFAULT)
        else:
            self._classifier_url = self.classifier_url
        self._cached_config: CachedConfig | None = None
        self._default_conversation: Conversation | None = None
        self._validate_and_cache()

    # ------------------------------------------------------------------
    # Initialization handshake
    # ------------------------------------------------------------------

    def _validate_and_cache(self) -> None:
        """Validate the API key and cache the user's routing config."""
        # Step 1: Validate API key
        try:
            validate_data = self._http.request_json("POST", "/api/sdk/validate")
        except ServoAPIError as e:
            if e.status_code in (401, 403):
                detail = e.body.get("error", str(e)) if isinstance(e.body, dict) else str(e)
                raise ServoAuthenticationError(
                    message=f"API key authentication failed: {detail}",
                    status_code=e.status_code,
                ) from e
            raise

        self._cached_config = CachedConfig.from_validate_response(validate_data)

        # Step 2: Fetch routing config
        try:
            routing_data = self._http.request_json("GET", "/api/sdk/routing-config")
            self._cached_config.routing_config = RoutingConfig.from_dict(routing_data)
        except ServoAPIError:
            # Routing config is optional — SDK can still function without it
            pass

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def config(self) -> CachedConfig | None:
        """The cached configuration from the init handshake."""
        return self._cached_config

    @property
    def user_id(self) -> str:
        """The authenticated user ID from the validated API key."""
        if self._cached_config is None:
            raise RuntimeError("SDK not initialised — no cached config available")
        return self._cached_config.user_id

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # API methods
    # ------------------------------------------------------------------

    def health(self) -> dict[str, Any]:
        return self._http.request_json("GET", "/health")

    def tiers(self) -> TiersResponse:
        data = self._http.request_json("GET", f"/tiers?user_id={self.user_id}")
        return TiersResponse.from_dict(data)

    def categories(self) -> CategoriesResponse:
        data = self._http.request_json("GET", f"/categories?user_id={self.user_id}")
        return CategoriesResponse.from_dict(data)

    def classify(
        self, prompt: str, *, use_quick: bool = False
    ) -> ClassificationResult:
        data = self._http.request_json(
            "POST",
            "/classify",
            json_body={"user_id": self.user_id, "prompt": prompt, "use_quick": bool(use_quick)},
        )
        return ClassificationResult.from_dict(data)

    def route(self, classification: ClassificationResult) -> RouteResponse:
        data = self._http.request_json(
            "POST",
            "/route",
            json_body={"user_id": self.user_id, "classification": classification.to_dict()},
        )
        return RouteResponse.from_dict(data)

    def send(
        self,
        request_message: str,
        *,
        use_quick_classify: bool = False,
        conversation: Conversation | None = None,
    ) -> ProcessingResult:
        """
        Calls `POST /process` on the backend.

        Returns full processing result including classification, routing, and LLM response.
        """
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
                "user_id": self.user_id,
                "prompt": prompt,
                "use_quick_classify": bool(use_quick_classify),
            },
        )
        return ProcessingResult.from_dict(data)

    def decompose(self, prompt: str) -> DecompositionResult:
        """
        Decompose a prompt into atomic subtasks using the local classifier model.

        Uses LangChain's with_structured_output() for schema-constrained JSON generation,
        analogous to outlines grammar-based constrained decoding.

        Raises ServoDecompositionError if the model returns output that does not conform
        to the DecompositionResult schema.
        Raises ServoConnectionError if the local model is unreachable.
        """
        llm = ChatOpenAI(
            model="local",
            base_url=self._classifier_url.rstrip("/") + "/v1",
            api_key="not-needed",
            temperature=0,
            timeout=self.timeout_s,
        )
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", _DECOMPOSE_SYSTEM_PROMPT),
            ("human", "{input}"),
        ])
        chain = prompt_template | llm.with_structured_output(
            DecompositionResult,
            method="json_schema",
        )
        try:
            return chain.invoke({"input": prompt})
        except Exception as e:
            raise ServoDecompositionError(
                message=f"Decomposition failed: {e}",
                raw_content=str(e),
            ) from e
