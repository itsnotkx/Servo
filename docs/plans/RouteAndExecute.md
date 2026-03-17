# Stage 5: `route_and_execute` — LLM Routing and Execution

## Context

The Servo Python SDK pipeline currently ends after Stage 4: `decompose_classify_and_embed()` returns `(ContextualizedDecompositionResult, ContextDB)` — subtasks with classified complexities and their texts embedded into an ephemeral ChromaDB vector store.

Stage 5 completes the pipeline: take those subtasks, resolve their dependency graph, dispatch each subtask to the correct LLM provider based on the user's `routing_config`, feed dependency outputs as context to downstream subtasks, and return a structured result.

---

## Files Modified

| File | Change |
|------|--------|
| `servo_sdk/errors.py` | Add `ServoRoutingError` |
| `servo_sdk/types.py` | Add `SubtaskExecutionResult`, `ExecutionResult` |
| `servo_sdk/client.py` | Add constructor fields, private helpers, `route_and_execute()`, convenience wrapper |
| `servo_sdk/__init__.py` | Export new types and error |
| `pyproject.toml` | Add optional provider extras |
| `tests/test_integration.py` | New tests for Stage 5 |

---

## Implementation Plan

### 1. `errors.py` — Add `ServoRoutingError`

Follows the `ServoEmbeddingError` pattern (non-frozen class, sets `__cause__`):

```python
class ServoRoutingError(ServoSDKError):
    def __init__(self, message: str, subtask_id: str | None = None, cause: Exception | None = None):
        super().__init__(f"Routing error: {message}")
        self.subtask_id = subtask_id
        self.__cause__ = cause
```

---

### 2. `types.py` — New result types

```python
@dataclass
class SubtaskExecutionResult:
    subtask_id: str
    subtask_text: str
    complexity_id: str           # category ID used (may be default fallback)
    model: str                   # RoutingCategory.model value actually used
    response: str                # raw text response from the LLM
    used_default_category: bool  # True if complexity_id had no matching category
    depends_on: list[str] = field(default_factory=list)  # needed for final_response

@dataclass
class ExecutionResult:
    subtask_results: list[SubtaskExecutionResult]

    @property
    def final_response(self) -> str:
        """Returns responses of terminal subtasks (those nothing else depends on).

        Single subtask → return its response directly.
        Multiple subtasks → identify terminal nodes (IDs not referenced in any depends_on),
        join their responses with double newlines.
        """
        if not self.subtask_results:
            return ""
        if len(self.subtask_results) == 1:
            return self.subtask_results[0].response
        dependency_ids: set[str] = set()
        for r in self.subtask_results:
            dependency_ids.update(r.depends_on)
        terminals = [r for r in self.subtask_results if r.subtask_id not in dependency_ids]
        return "\n\n".join(t.response for t in terminals)
```

---

### 3. `client.py` — Core changes

#### 3a. New constructor fields (add to `Servo` dataclass)

```python
provider_api_keys: dict[str, str] = field(default_factory=dict)
# e.g. {'google': 'AIza...', 'openai': 'sk-...', 'anthropic': 'sk-ant-...'}

custom_endpoints: dict[str, str] = field(default_factory=dict)
# keyed by category ID: {'local': 'http://localhost:11434/v1'}
```

In `__post_init__`, also initialise: `self._db_lock: threading.Lock = threading.Lock()`

New top-level imports: `import threading` and `from concurrent.futures import ThreadPoolExecutor`

#### 3b. `_detect_provider(model: str) -> str`

Case-insensitive prefix matching on `RoutingCategory.model`:

| Model prefix | Provider |
|---|---|
| `gemini-*`, `gemma-*` | `"google"` |
| `claude-*` | `"anthropic"` |
| `gpt-*`, `o1-*`, `o3-*`, `o4-*` | `"openai"` |
| anything else | `"openai_compatible"` |

#### 3c. `_resolve_category(complexity_id: str) -> tuple[RoutingCategory, bool]`

Returns `(category, used_default)`. Looks up by `complexity_id`; if not found, falls back to `default_category_id`. Raises `ServoRoutingError` if the default is also missing (degenerate config).

#### 3d. `_build_llm(category: RoutingCategory) -> BaseChatModel`

Uses **lazy imports** to avoid hard dependency on all provider packages. Per provider:

- **`"google"`**: `from langchain_google_genai import ChatGoogleGenerativeAI`; key from `provider_api_keys.get("google")` or `GOOGLE_AI_STUDIO_API_KEY` env var.
- **`"anthropic"`**: `from langchain_anthropic import ChatAnthropic`; key from `provider_api_keys.get("anthropic")` or `ANTHROPIC_API_KEY` env var.
- **`"openai"`**: `ChatOpenAI` (already imported at top); key from `provider_api_keys.get("openai")` or `OPENAI_API_KEY` env var.
- **`"openai_compatible"`**: `ChatOpenAI` with `base_url=custom_endpoints[category.id]`. Raises `ServoRoutingError` if no endpoint is configured for that category ID.

All branches raise `ServoRoutingError` if API key is missing or provider package is not installed.

#### 3e. `_build_execution_messages(subtask_text: str, context: list[str]) -> list[tuple]`

Builds LangChain `(role, content)` message tuples. If `context` is non-empty, prepends a system message listing the dependency outputs as numbered blocks:

```
You are a helpful assistant executing one step in a multi-step pipeline.
The following are outputs from upstream steps that your task depends on:

[Dependency 1]:
<context>

Use this context to complete your assigned task.
```

If no context, system message is simply: `"You are a helpful assistant. Complete the following task."`

#### 3f. `_execute_subtask(subtask, db, lock) -> SubtaskExecutionResult`

1. `_resolve_category(subtask.complexity_id)` → `(category, used_default)`
2. `db.get_context_for(subtask.depends_on)` (read, no lock needed)
3. `_build_llm(category)` + `_build_execution_messages(subtask.text, context)` → invoke chain
4. `with lock: db.add(subtask.id, response_text)` (lock prevents concurrent write corruption)
5. Return `SubtaskExecutionResult`

**Thread-safety note**: ChromaDB's `EphemeralClient` is in-memory. The lock serialises `db.add()` calls from parallel threads. Reads (`get_context_for`) don't need the lock because wave scheduling guarantees all prior-wave writes are complete before any next-wave reads begin.

#### 3g. `_compute_waves(subtasks) -> list[list[ContextualizedSubtask]]`

Kahn's algorithm. Returns a list of waves, each wave being a set of subtasks whose dependencies all appear in earlier waves. Raises `ServoRoutingError("Dependency graph contains a cycle")` if scheduled count ≠ total subtask count.

#### 3h. `route_and_execute(contextualized, db, *, max_workers=4) -> ExecutionResult`

```python
waves = _compute_waves(contextualized.subtasks)
lock = self._db_lock

all_results: list[SubtaskExecutionResult] = []
with ThreadPoolExecutor(max_workers=max_workers) as executor:
    for wave in waves:
        futures = [executor.submit(_execute_subtask, s, db, lock) for s in wave]
        for f in futures:
            all_results.append(f.result())  # blocks until whole wave completes

return ExecutionResult(subtask_results=all_results)
```

The inner `for f in futures: f.result()` collects **all** Wave N results before the loop advances to Wave N+1 — this is the wave barrier. It ensures every ContextDB write from Wave N is complete before Wave N+1 reads context.

Raises `ServoDecompositionError` if routing config is unavailable.

#### 3i. `decompose_classify_embed_and_execute(prompt, *, timeout_s=60.0, max_workers=4) -> ExecutionResult`

Convenience full-pipeline wrapper:
```python
contextualized, db = self.decompose_classify_and_embed(prompt, timeout_s=timeout_s)
return self.route_and_execute(contextualized, db, max_workers=max_workers)
```

---

### 4. `pyproject.toml` — Optional provider extras

```toml
[project.optional-dependencies]
dev = ["pytest>=8.0"]
google = ["langchain-google-genai>=2.0"]
anthropic = ["langchain-anthropic>=0.1"]
all-providers = ["langchain-google-genai>=2.0", "langchain-anthropic>=0.1"]
```

`langchain-google-genai` and `langchain-anthropic` are **not** added to mandatory `dependencies` — consistent with the lazy-import approach. Users install only what they need (`pip install servo-sdk[google]`).

---

### 5. `__init__.py` — Export new symbols

Add to imports and `__all__`:
- `ServoRoutingError` (from `.errors`)
- `SubtaskExecutionResult`, `ExecutionResult` (from `.types`)

---

### 6. Tests in `tests/test_integration.py`

#### `test_route_and_execute_mock_llm`
- DAG: `task-A` (no deps) → `task-B` (depends on A)
- `monkeypatch` `_build_llm` to return a fake chain echoing `"response for <id>"`
- Assert: execution order correct, `db.get_by_id("task-A") == "response for task-A"`, `result.final_response == "response for task-B"` (terminal node only)

#### `test_route_and_execute_fallback_to_default`
- Subtask with `complexity_id="nonexistent_tier"`, routing config `default_category_id="simple"`
- Assert: `used_default_category == True` and `complexity_id == "simple"` in result

#### `test_route_and_execute_parallel_wave`
- 4 independent subtasks (no deps) → all in Wave 0
- Mock LLM with slight sleep to stress concurrent writes
- Assert: all 4 IDs in ContextDB with correct responses after execution

#### `test_route_and_execute_live` *(skipped unless key set)*
```python
@pytest.mark.skipif(not os.environ.get("GOOGLE_AI_STUDIO_API_KEY"), reason="...")
def test_route_and_execute_live(client):
    result = client.decompose_classify_embed_and_execute(
        "Summarise this article, then translate the summary into Spanish."
    )
    assert len(result.subtask_results) > 0
    assert result.final_response.strip() != ""
```

---

## Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Provider detection | Case-insensitive prefix on `RoutingCategory.model` | Matches user strings like `"Gemini-3-Pro"`, `"Claude-Opus-4.5"`, `"GPT-4"` without schema changes |
| Missing category | Silent fallback to `default_category_id`, flagged via `used_default_category=True` | Graceful degradation; avoids hard failure for misconfigured categories |
| ContextDB thread safety | `threading.Lock` around `db.add()` only | Reads are safe; writes from parallel wave threads are serialised |
| `final_response` | Terminal node detection via `depends_on` graph topology | Correct for any DAG shape (linear, fan-in, fan-out) |
| Provider imports | Lazy inside `_build_llm`; not in mandatory deps | Users only install the provider SDK they need |
| Wave barrier | Collect all per-wave futures and call `.result()` before next wave | Guarantees all Wave N ContextDB writes complete before Wave N+1 reads |
| API keys | Env vars (`GOOGLE_AI_STUDIO_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`) with constructor override | Consistent with existing `CLASSIFIER_ENDPOINT` env var pattern |
| Custom endpoints | Per category-ID in `custom_endpoints` dict | Allows different local models per tier without schema changes |

---

## Verification

```bash
# Unit tests (no network required)
pytest tests/test_integration.py -k "mock or fallback or parallel"

# Live test (requires GOOGLE_AI_STUDIO_API_KEY)
pytest tests/test_integration.py -k "live"

# Import check
python -c "from servo_sdk import Servo, ExecutionResult, ServoRoutingError; print('OK')"

# Missing key raises helpful error
python -c "
from servo_sdk import Servo, ContextualizedDecompositionResult
# ... construct client, call route_and_execute with google model → ServoRoutingError
"
```
