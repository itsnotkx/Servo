from __future__ import annotations

import json
import os
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any

import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda

from ._http import HTTPClient
from .context import Conversation
from .errors import ServoAPIError, ServoAuthenticationError, ServoDecompositionError, ServoEmbeddingError, ServoRoutingError
from .types import (
    CachedConfig,
    ClassificationResult,
    ClassifiedDecompositionResult,
    ClassifiedSubtask,
    ContextualizedDecompositionResult,
    ContextualizedSubtask,
    ExecutionResult,
    ProcessingResult,
    RouteResponse,
    RoutingCategory,
    RoutingConfig,
    SubtaskExecutionResult,
    TiersResponse,
    CategoriesResponse,
    Subtask,
    DecompositionResult,
)

class ContextDB:
    """
    Ephemeral per-prompt ChromaDB vector store.
    Created fresh for each decompose_classify_and_embed() call.

    Lifecycle:
      Stage 4: subtask texts are embedded and stored by ID.
      Stage 5: model responses overwrite entries via add();
               subtasks retrieve their dependency responses via get_context_for().
    """

    def __init__(self, embedding_fn: DefaultEmbeddingFunction) -> None:
        self._client = chromadb.EphemeralClient()
        self._collection_name = f"subtasks_{uuid.uuid4().hex}"
        self._collection = self._client.create_collection(
            name=self._collection_name,
            embedding_function=embedding_fn,
        )

    def add(self, subtask_id: str, content: str) -> None:
        """Embed and store (or overwrite) content for a given subtask ID."""
        existing = self._collection.get(ids=[subtask_id])
        if existing["ids"]:
            self._collection.update(ids=[subtask_id], documents=[content])
        else:
            self._collection.add(ids=[subtask_id], documents=[content])

    def get_by_id(self, subtask_id: str) -> str | None:
        """Exact ID lookup — used for dependency resolution."""
        result = self._collection.get(ids=[subtask_id])
        docs = result.get("documents") or []
        return docs[0] if docs else None

    def get_context_for(self, depends_on: list[str]) -> list[str]:
        """Return stored content for each dependency ID that exists in the DB."""
        if not depends_on:
            return []
        result = self._collection.get(ids=depends_on)
        return result.get("documents") or []

    def close(self) -> None:
        """Delete the in-memory collection to release resources immediately."""
        try:
            self._client.delete_collection(self._collection_name)
        except Exception:
            pass

    def search(self, query: str, k: int = 3) -> list[str]:
        """Semantic similarity search by text query. Used by Stage 5+ for fuzzy retrieval."""
        count = self._collection.count()
        if count == 0:
            return []
        results = self._collection.query(
            query_texts=[query],
            n_results=min(k, count),
        )
        return (results.get("documents") or [[]])[0]


_SERVO_ENDPOINT = "https://servo.example.com"  # TODO: set to real prod URL
_CLASSIFIER_DEFAULT = "http://localhost:8080"

_DECOMPOSE_SYSTEM_PROMPT = (
    "You are a task decomposition assistant. "
    "Given a user prompt, break it into atomic, non-overlapping subtasks. "
    "Simple prompts need only one subtask; complex prompts may need up to five. "
    "Use 'dependsOn' to express task dependencies by referencing other subtask IDs."
)

_CLASSIFY_SYSTEM_PROMPT_TEMPLATE = (
    "You are a task complexity classifier. "
    "Given a list of subtasks, assign each one the most appropriate complexity category.\n\n"
    "Available categories:\n{categories}\n\n"
    "For each subtask, choose the category whose description best matches the subtask's difficulty."
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
    provider_api_keys: dict[str, str] = field(default_factory=dict)
    # e.g. {'google': 'AIza...', 'openai': 'sk-...', 'anthropic': 'sk-ant-...'}
    custom_endpoints: dict[str, str] = field(default_factory=dict)
    # keyed by category ID: {'local': 'http://localhost:11434/v1'}

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
        self._embedding_fn_cache: DefaultEmbeddingFunction | None = None
        self._db_lock: threading.Lock = threading.Lock()
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
    def _embedding_fn(self) -> DefaultEmbeddingFunction:
        """Lazy-init and cache the fastembed embedding function for the client's lifetime."""
        if self._embedding_fn_cache is None:
            self._embedding_fn_cache = DefaultEmbeddingFunction()
        return self._embedding_fn_cache

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

    def decompose_and_classify(self, prompt: str) -> ClassifiedDecompositionResult:
        """
        Decompose a prompt into subtasks and classify each by complexity in one
        continuous LCEL pipeline.

        The chain runs two sequential LLM calls through the local classifier:
          1. Decompose the prompt → DecompositionResult
          2. Classify every subtask → ClassifiedDecompositionResult

        Each subtask in the result gains `complexity_id` (a routing config category ID)
        and `complexity_reasoning` (a one-sentence justification).

        Raises ServoDecompositionError if the routing config is unavailable or if
        either LLM call fails.
        """
        if self._cached_config is None or self._cached_config.routing_config is None:
            raise ServoDecompositionError(
                message="Routing config not available for classification",
                raw_content="",
            )

        categories_str = "\n".join(
            f"- {c.id}: {c.name} — {c.description}"
            for c in self._cached_config.routing_config.categories
        )

        llm = ChatOpenAI(
            model="local",
            base_url=self._classifier_url.rstrip("/") + "/v1",
            api_key="not-needed",
            temperature=0,
            timeout=self.timeout_s,
        )
        decompose_prompt = ChatPromptTemplate.from_messages([
            ("system", _DECOMPOSE_SYSTEM_PROMPT),
            ("human", "{input}"),
        ])
        classify_prompt = ChatPromptTemplate.from_messages([
            ("system", _CLASSIFY_SYSTEM_PROMPT_TEMPLATE.format(categories=categories_str)),
            ("human", "{input}"),
        ])

        def _to_classify_input(decomp: DecompositionResult) -> dict:
            return {
                "input": json.dumps(
                    {"subtasks": [s.model_dump(by_alias=True) for s in decomp.subtasks]}
                )
            }

        chain = (
            decompose_prompt
            | llm.with_structured_output(DecompositionResult, method="json_schema")
            | RunnableLambda(_to_classify_input)
            | classify_prompt
            | llm.with_structured_output(ClassifiedDecompositionResult, method="json_schema")
        )

        try:
            return chain.invoke({"input": prompt})
        except Exception as e:
            raise ServoDecompositionError(
                message=f"Decompose-and-classify failed: {e}",
                raw_content=str(e),
            ) from e

    def embed_and_contextualize(
        self,
        classified: ClassifiedDecompositionResult,
    ) -> tuple[ContextualizedDecompositionResult, ContextDB]:
        """
        Step 3 in the pipeline: embed all subtask texts into an ephemeral ChromaDB ContextDB.

        Returns:
            - ContextualizedDecompositionResult: subtasks with empty context lists
              (to be filled by Stage 5 as model responses arrive)
            - ContextDB: live vector store to pass into the Stage 5 routing loop
        """
        try:
            db = ContextDB(self._embedding_fn)

            for subtask in classified.subtasks:
                db.add(subtask.id, subtask.text)

            contextualized_subtasks = [
                ContextualizedSubtask(**subtask.model_dump(), context=[])
                for subtask in classified.subtasks
            ]

            return ContextualizedDecompositionResult(subtasks=contextualized_subtasks), db

        except Exception as exc:
            raise ServoEmbeddingError(str(exc), cause=exc) from exc

    def decompose_classify_and_embed(
        self,
        prompt: str,
        *,
        timeout_s: float = 60.0,
    ) -> tuple[ContextualizedDecompositionResult, ContextDB]:
        """
        Full pipeline: decompose → classify → embed.
        Returns contextualized subtasks (empty context) + live ContextDB for Stage 5.
        """
        classified = self.decompose_and_classify(prompt)
        return self.embed_and_contextualize(classified)

    # ------------------------------------------------------------------
    # Stage 5: Route and Execute
    # ------------------------------------------------------------------

    @staticmethod
    def _detect_provider(model: str) -> str:
        """Infer the LLM provider from a model name string."""
        m = model.lower()
        if m.startswith(("gemini-", "gemma-")):
            return "google"
        if m.startswith("claude-"):
            return "anthropic"
        if m.startswith(("gpt-", "o1-", "o3-", "o4-")):
            return "openai"
        return "openai_compatible"

    def _resolve_category(self, complexity_id: str) -> tuple[RoutingCategory, bool]:
        """Return (category, used_default). Falls back to default_category_id if not found."""
        if self._cached_config is None or self._cached_config.routing_config is None:
            raise ServoDecompositionError(
                message="Routing config not available",
                raw_content="",
            )
        config = self._cached_config.routing_config
        by_id = {c.id: c for c in config.categories}

        if complexity_id in by_id:
            return by_id[complexity_id], False

        default_id = config.default_category_id
        if default_id in by_id:
            return by_id[default_id], True

        raise ServoRoutingError(
            message=f"Neither complexity_id '{complexity_id}' nor default_category_id '{default_id}' found in routing config"
        )

    def _build_llm(self, category: RoutingCategory):
        """Lazily import and construct the correct LangChain chat model for a category."""
        provider = self._detect_provider(category.model)

        if provider == "google":
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI  # type: ignore
            except ImportError as e:
                raise ServoRoutingError(
                    message="langchain-google-genai is not installed. Run: pip install servo-sdk[google]",
                    cause=e,
                ) from e
            api_key = self.provider_api_keys.get("google") or os.environ.get("GOOGLE_AI_STUDIO_API_KEY")
            if not api_key:
                raise ServoRoutingError(
                    message="No API key for Google. Set GOOGLE_AI_STUDIO_API_KEY or pass provider_api_keys={'google': '...'}"
                )
            return ChatGoogleGenerativeAI(model=category.model, google_api_key=api_key)

        if provider == "anthropic":
            try:
                from langchain_anthropic import ChatAnthropic  # type: ignore
            except ImportError as e:
                raise ServoRoutingError(
                    message="langchain-anthropic is not installed. Run: pip install servo-sdk[anthropic]",
                    cause=e,
                ) from e
            api_key = self.provider_api_keys.get("anthropic") or os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise ServoRoutingError(
                    message="No API key for Anthropic. Set ANTHROPIC_API_KEY or pass provider_api_keys={'anthropic': '...'}"
                )
            return ChatAnthropic(model=category.model, anthropic_api_key=api_key)

        if provider == "openai":
            api_key = self.provider_api_keys.get("openai") or os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ServoRoutingError(
                    message="No API key for OpenAI. Set OPENAI_API_KEY or pass provider_api_keys={'openai': '...'}"
                )
            return ChatOpenAI(model=category.model, api_key=api_key)

        # openai_compatible — requires a custom endpoint configured per category ID
        endpoint = self.custom_endpoints.get(category.id)
        if not endpoint:
            raise ServoRoutingError(
                message=f"No custom endpoint configured for category '{category.id}'. "
                        f"Pass custom_endpoints={{'{category.id}': 'http://...'}}",
                subtask_id=None,
            )
        return ChatOpenAI(model=category.model, base_url=endpoint, api_key="not-needed")

    @staticmethod
    def _build_execution_messages(subtask_text: str, context: list[str]) -> list:
        """Build LangChain messages for a subtask, injecting dependency outputs as context."""
        if context:
            context_blocks = "\n\n".join(
                f"[Dependency {i + 1}]:\n{c}" for i, c in enumerate(context)
            )
            system_content = (
                "You are a helpful assistant executing one step in a multi-step pipeline.\n"
                "The following are outputs from upstream steps that your task depends on:\n\n"
                f"{context_blocks}\n\n"
                "Use this context to complete your assigned task."
            )
        else:
            system_content = "You are a helpful assistant. Complete the following task."

        return [SystemMessage(content=system_content), HumanMessage(content=subtask_text)]

    def _execute_subtask(
        self,
        subtask: ContextualizedSubtask,
        db: ContextDB,
        lock: threading.Lock,
    ) -> SubtaskExecutionResult:
        """Execute a single subtask: resolve category, fetch context, call LLM, write result."""
        category, used_default = self._resolve_category(subtask.complexity_id)
        context = db.get_context_for(subtask.depends_on)
        llm = self._build_llm(category)
        messages = self._build_execution_messages(subtask.text, context)

        try:
            response = llm.invoke(messages)
            response_text: str = response.content
        except ServoRoutingError:
            raise
        except Exception as e:
            raise ServoRoutingError(
                message=f"LLM invocation failed: {e}",
                subtask_id=subtask.id,
                cause=e,
            ) from e

        with lock:
            db.add(subtask.id, response_text)

        return SubtaskExecutionResult(
            subtask_id=subtask.id,
            subtask_text=subtask.text,
            complexity_id=category.id,
            model=category.model,
            response=response_text,
            used_default_category=used_default,
            depends_on=list(subtask.depends_on),
        )

    @staticmethod
    def _compute_waves(subtasks: list[ContextualizedSubtask]) -> list[list[ContextualizedSubtask]]:
        """Kahn's algorithm: returns subtasks grouped into dependency-ordered waves."""
        id_to_subtask = {s.id: s for s in subtasks}
        in_degree = {s.id: 0 for s in subtasks}
        dependents: dict[str, list[str]] = {s.id: [] for s in subtasks}

        for s in subtasks:
            for dep in s.depends_on:
                in_degree[s.id] += 1
                dependents[dep].append(s.id)

        ready = [s for s in subtasks if in_degree[s.id] == 0]
        waves: list[list[ContextualizedSubtask]] = []
        scheduled = 0

        while ready:
            waves.append(ready)
            scheduled += len(ready)
            next_ready: list[ContextualizedSubtask] = []
            for s in ready:
                for dep_id in dependents[s.id]:
                    in_degree[dep_id] -= 1
                    if in_degree[dep_id] == 0:
                        next_ready.append(id_to_subtask[dep_id])
            ready = next_ready

        if scheduled != len(subtasks):
            raise ServoRoutingError(message="Dependency graph contains a cycle")

        return waves

    def route_and_execute(
        self,
        contextualized: ContextualizedDecompositionResult,
        db: ContextDB,
        *,
        max_workers: int = 4,
    ) -> ExecutionResult:
        """
        Stage 5: dispatch each subtask to its routed LLM, respecting the dependency DAG.

        Subtasks with no mutual dependencies run in parallel within each wave.
        Each wave completes fully before the next wave begins, ensuring dependency
        outputs are written to ContextDB before downstream subtasks read them.
        """
        if self._cached_config is None or self._cached_config.routing_config is None:
            raise ServoDecompositionError(
                message="Routing config not available for execution",
                raw_content="",
            )

        waves = self._compute_waves(contextualized.subtasks)
        lock = self._db_lock
        all_results: list[SubtaskExecutionResult] = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for wave in waves:
                futures = [executor.submit(self._execute_subtask, s, db, lock) for s in wave]
                for f in futures:
                    all_results.append(f.result())  # blocks until whole wave completes

        return ExecutionResult(subtask_results=all_results)

    def decompose_classify_embed_and_execute(
        self,
        prompt: str,
        *,
        timeout_s: float = 60.0,
        max_workers: int = 4,
    ) -> ExecutionResult:
        """
        Full pipeline convenience wrapper: decompose → classify → embed → route & execute.
        Cleans up the ContextDB after execution.
        """
        contextualized, db = self.decompose_classify_and_embed(prompt, timeout_s=timeout_s)
        try:
            return self.route_and_execute(contextualized, db, max_workers=max_workers)
        finally:
            db.close()
