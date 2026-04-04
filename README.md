# Servo

**Intelligent LLM routing that cuts inference costs by up to 80%.**

Servo classifies every prompt by complexity and routes it to the cheapest model that can handle it — without sacrificing response quality. Simple factual questions go to lightweight models; complex multi-step reasoning goes to powerful ones. You pay only for what each task actually needs.

---

## How it works

```
prompt → decompose → classify complexity → route to model → execute → response
                                                                    ↓
                                                         cost + savings tracked
```

1. **Decompose** — breaks complex prompts into atomic, dependency-aware subtasks
2. **Classify** — assigns each subtask a complexity tier (e.g., `simple`, `complex`)
3. **Route** — maps each tier to the cheapest appropriate model in your routing config
4. **Execute** — dispatches subtasks to their routed LLMs in parallel, respecting the dependency DAG
5. **Track** — records per-subtask cost, savings, latency, and token counts automatically

---

## SDKs

| Language | Package | Install |
|----------|---------|---------|
| Python 3.10+ | `servo-sdk` | `pip install servo-sdk` |
| JavaScript / TypeScript | `servo-sdk` | `npm install servo-sdk` |

---

## Python SDK

### Installation

```bash
pip install servo-sdk
```

For specific LLM providers:

```bash
pip install servo-sdk[google]        # Gemini / Gemma
pip install servo-sdk[anthropic]     # Claude
pip install servo-sdk[all-providers] # all of the above
```

### Quick start

```python
from servo_sdk import Servo

client = Servo(
    api_key="sk_live_...",
    provider_api_keys={"google": "AIza..."},
)

# Full pipeline: decompose → classify → route → execute
result = client.decompose_classify_embed_and_execute(
    "Compare the pros and cons of React, Vue, and Svelte, "
    "then recommend one for a small team building a dashboard."
)

print(result.final_response)
print(f"Cost:    ${result.total_cost:.6f}")
print(f"Savings: ${result.total_savings:.6f}")
```

### Simple send (no decomposition)

```python
result = client.send("Who was the first president of the United States?")

print(result.classification.category_id)  # 'simple'
print(result.target_model)                # e.g., 'gemma-3-27b-it'
print(result.llm_response)
```

### Step-by-step pipeline

```python
# 1. Decompose and classify subtasks
classified = client.decompose_and_classify(
    "Write a market analysis for electric vehicles — TAM/SAM/SOM and a competitor breakdown."
)
for subtask in classified.subtasks:
    print(f"[{subtask.complexity_id}] {subtask.text}")

# 2. Embed into vector store (for dependency-aware context passing)
contextualized, db = client.embed_and_contextualize(classified)

# 3. Route and execute (parallel where dependencies allow)
result = client.route_and_execute(contextualized, db, original_prompt="...")
db.close()

# Per-subtask breakdown
for r in result.subtask_results:
    print(f"[{r.model}] {r.subtask_text}")
    print(f"  latency={r.latency_ms}ms  tokens={r.input_tokens}+{r.output_tokens}  cost=${r.cost:.6f}")
```

### Conversation context

```python
from servo_sdk.context import Conversation

conversation = Conversation(system_prompt="You are a helpful assistant.")
conversation.add_user("What is LangChain?")
conversation.add_assistant("LangChain is a framework for building LLM applications...")

result = client.send("How does it compare to LlamaIndex?", conversation=conversation)
```

### Configuration

```python
client = Servo(
    api_key="sk_live_...",

    # Provider API keys (or use env vars: GOOGLE_AI_STUDIO_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY)
    provider_api_keys={
        "google":    "AIza...",
        "anthropic": "sk-ant-...",
        "openai":    "sk-...",
    },

    # Custom OpenAI-compatible endpoints, keyed by routing category ID
    custom_endpoints={
        "local": "http://localhost:11434/v1",
    },

    # Local Llama.cpp classifier for decomposition (or set CLASSIFIER_ENDPOINT)
    classifier_url="http://localhost:8080",

    # Telemetry: "async" (default) | "sync" | "off"
    telemetry_mode="async",

    timeout_s=60.0,
)
```

### Error handling

```python
from servo_sdk.errors import (
    ServoAuthenticationError,
    ServoDecompositionError,
    ServoRoutingError,
    ServoEmbeddingError,
)

try:
    result = client.decompose_classify_embed_and_execute("Summarise the latest AI research.")
except ServoAuthenticationError:
    print("Invalid API key")
except ServoDecompositionError as e:
    print(f"Decomposition failed: {e}")
except ServoRoutingError as e:
    print(f"Routing/execution failed: {e}")
```

---

## JavaScript / TypeScript SDK

### Installation

```bash
npm install servo-sdk
```

Requires Node.js 18+ (native fetch).

### Quick start

```javascript
import { Servo } from 'servo-sdk';

const client = new Servo({ apiKey: 'sk_live_...' });

const result = await client.send('What is machine learning?');

console.log(result.classification.category_id);  // 'simple'
console.log(result.target_model);                // e.g., 'gemma-3-27b-it'
console.log(result.llm_response);
```

### Step-by-step

```javascript
// Classify
const classification = await client.classify('Explain quantum entanglement');
console.log(classification.category_id);   // 'complex'
console.log(classification.confidence);    // 0.92

// Route
const routing = await client.route(classification);
console.log(routing.target_model);         // 'gemini-2.5-flash'
```

### Conversation context

```javascript
import { Servo, Conversation } from 'servo-sdk';

const client = new Servo({ apiKey: 'sk_live_...' });
const conv = new Conversation('You are a helpful assistant.');

conv.addUser('What is TypeScript?');
conv.addAssistant('TypeScript is a typed superset of JavaScript...');

const result = await client.send('What are its main benefits?', { conversation: conv });
```

### Error handling

```javascript
import { ServoAPIError, ServoConnectionError } from 'servo-sdk';

try {
  const result = await client.send('test');
} catch (error) {
  if (error instanceof ServoAPIError) {
    console.error('API error:', error.statusCode, error.body);
  } else if (error instanceof ServoConnectionError) {
    console.error('Connection error:', error.message);
  }
}
```

---

## API reference

### Python — `Servo`

| Method | Description |
|--------|-------------|
| `send(prompt, *, use_quick_classify, conversation)` | Classify + route + call LLM in one request |
| `classify(prompt, *, use_quick)` | Classify a prompt into a complexity tier |
| `route(classification)` | Resolve a classification to a target model |
| `decompose(prompt)` | Break a prompt into atomic subtasks |
| `decompose_and_classify(prompt)` | Decompose + classify subtasks in one chain |
| `embed_and_contextualize(classified)` | Embed subtasks into an ephemeral vector store |
| `decompose_classify_and_embed(prompt)` | Decompose + classify + embed |
| `route_and_execute(contextualized, db, *, max_workers, original_prompt)` | Dispatch subtasks to LLMs, respecting the dependency DAG; emits telemetry |
| `decompose_classify_embed_and_execute(prompt)` | Full pipeline convenience wrapper |
| `health()` | Check backend health |
| `tiers()` | Get category → model mapping |
| `categories()` | Get full category metadata |

### JavaScript — `Servo`

| Method | Description |
|--------|-------------|
| `send(prompt, userId?, options?)` | Classify + route + call LLM in one request |
| `classify(prompt, userId?, useQuick?)` | Classify a prompt |
| `route(classification, userId?)` | Route a classification to a model |
| `health()` | Check backend health |
| `tiers(userId?)` | Get category → model mapping |
| `categories(userId?)` | Get full category metadata |
| `withConversation(conv?)` | Initialize or retrieve a `Conversation` |

---

## Key types

### `ExecutionResult` (Python)

```python
@dataclass
class ExecutionResult:
    subtask_results: list[SubtaskExecutionResult]
    total_latency_ms: int    # wall-clock time for the full pipeline (ms)
    total_cost: float        # total USD cost across all subtasks
    total_savings: float     # USD saved vs routing everything to the most expensive model

    @property
    def final_response(self) -> str: ...  # concatenated responses in execution order
```

### `SubtaskExecutionResult` (Python)

```python
@dataclass
class SubtaskExecutionResult:
    subtask_id: str
    subtask_text: str
    complexity_id: str           # routing tier used (may be default fallback)
    model: str                   # model actually invoked
    response: str
    used_default_category: bool
    depends_on: list[str]
    latency_ms: int
    input_tokens: int
    output_tokens: int
    cost: float                  # USD cost for this subtask
    cost_savings: float          # USD saved vs baseline (most expensive model)
```

### `ProcessingResult` (both SDKs)

```typescript
{
  classification: ClassificationResult;  // { category_id, category_name, confidence, reasoning, requires_chunking }
  target_model: string;
  selected_category: ClassificationCategory;
  llm_response: string | null;
}
```

---

## Telemetry

The SDK automatically sends execution traces back to the Servo backend after each `route_and_execute` call. This powers the cost and savings dashboards in the Servo web app.

| Mode | Behaviour |
|------|-----------|
| `"async"` (default) | Fire-and-forget in a daemon thread — never blocks your code |
| `"sync"` | Waits for the POST to complete — useful in short-lived scripts |
| `"off"` | Disables telemetry entirely |

```python
client = Servo(api_key="...", telemetry_mode="off")
```

---

## Development

### Python SDK

```bash
cd "SDK/Python SDK"
pip install -e ".[dev]"
pytest
```

### JavaScript SDK

```bash
cd "SDK/NPM SDK"
npm install
npm run build
```

---
