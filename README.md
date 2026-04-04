# Servo

**Intelligent LLM routing that cuts inference costs by up to 80%.**

Servo classifies every prompt by complexity and routes it to the cheapest model that can handle it — without sacrificing response quality. Simple factual questions go to lightweight models; complex multi-step reasoning goes to powerful ones. You pay only for what you need.

---

## How it works

```
prompt → decompose → classify complexity → route to model → execute → response
```

1. **Decompose** — breaks complex prompts into atomic subtasks
2. **Classify** — assigns each subtask a complexity tier (e.g., `simple`, `complex`)
3. **Route** — maps each tier to the cheapest appropriate model in your config
4. **Execute** — dispatches subtasks to their routed LLMs in parallel, respecting dependencies

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
pip install servo-sdk[google]       # Gemini / Gemma
pip install servo-sdk[anthropic]    # Claude
pip install servo-sdk[all-providers]
```

### Quick start

```python
from servo_sdk import Servo

client = Servo(
    api_key="sk_live_...",
    provider_api_keys={"google": "AIza..."},
)

# Single-call pipeline: decompose → classify → route → execute
result = client.decompose_classify_embed_and_execute(
    "Compare the pros and cons of React, Vue, and Svelte, "
    "then recommend one for a small team building a dashboard."
)

for subtask in result.subtask_results:
    print(f"[{subtask.model}] {subtask.subtask_text}")
    print(subtask.response)
    print()
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
# 1. Decompose and classify
classified = client.decompose_and_classify(
    "Write a market analysis for electric vehicles, "
    "including TAM/SAM/SOM and a competitor breakdown."
)

for subtask in classified.subtasks:
    print(f"{subtask.id}: [{subtask.complexity_id}] {subtask.text}")

# 2. Embed subtasks into vector store (for dependency context)
contextualized, db = client.embed_and_contextualize(classified)

# 3. Route and execute (parallel where dependencies allow)
result = client.route_and_execute(contextualized, db)
db.close()
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

    # Provider API keys (or set env vars: GOOGLE_AI_STUDIO_API_KEY, etc.)
    provider_api_keys={
        "google": "AIza...",
        "anthropic": "sk-ant-...",
        "openai": "sk-...",
    },

    # Custom OpenAI-compatible endpoints, keyed by routing category ID
    custom_endpoints={
        "local": "http://localhost:11434/v1",
    },

    # Local Llama.cpp classifier (or set CLASSIFIER_ENDPOINT env var)
    classifier_url="http://localhost:8080",

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
    result = client.send("Hello")
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
| `embed_and_contextualize(classified)` | Embed subtasks into vector store |
| `decompose_classify_and_embed(prompt)` | Decompose + classify + embed |
| `route_and_execute(contextualized, db)` | Dispatch subtasks to LLMs, respecting the dependency DAG |
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

### `ProcessingResult`

```typescript
{
  classification: ClassificationResult;
  target_model: string;
  selected_category: ClassificationCategory;
  llm_response: string | null;
  chunks?: string[];
  requires_aggregation?: boolean;
}
```

### `ClassificationResult`

```typescript
{
  category_id: string;      // e.g., 'simple', 'complex'
  category_name: string;
  reasoning: string;
  confidence: number;       // 0.0 – 1.0
  requires_chunking: boolean;
}
```

### `ExecutionResult` (Python only)

```python
@dataclass
class ExecutionResult:
    subtask_results: list[SubtaskExecutionResult]

@dataclass
class SubtaskExecutionResult:
    subtask_id: str
    subtask_text: str
    complexity_id: str
    model: str
    response: str
    used_default_category: bool
    depends_on: list[str]
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