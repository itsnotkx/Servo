# Right-Sizing Inference Workflow

A Python-based prompt classification and routing system that directs prompts to appropriate LLMs based on complexity.

## Overview

```
┌─────────────┐     ┌────────────┐     ┌─────────┐     ┌──────────────┐
│   Prompt    │ ──▶ │  Chunker   │ ──▶ │Classifier│ ──▶ │    Router    │
│             │     │(if needed) │     │(Qwen3-14B)│    │(Tier-based)  │
└─────────────┘     └────────────┘     └─────────┘     └──────────────┘
                                                              │
                                                              ▼
                                                       Target Model
```

The workflow:
1. **Chunks** long prompts using LlamaIndex (semantic or recursive splitting)
2. **Classifies** prompt complexity using Instructor + Qwen3-14B
3. **Routes** to the appropriate model tier

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

All settings are configurable via `.env.local` in the **project root**:

```bash
# Classifier Model Endpoint (Qwen3-14B via Llama.cpp)
CLASSIFIER_ENDPOINT=http://localhost:8080/v1
CLASSIFIER_MODEL=qwen3-14b
CLASSIFIER_TEMPERATURE=0.1

# Tier Models
TIER_SIMPLE_MODEL=qwen-0.5b
TIER_MEDIUM_MODEL=qwen-7b
TIER_COMPLEX_MODEL=qwen-14b
TIER_LONG_CONTEXT_MODEL=qwen-14b-128k
TIER_CODE_MODEL=qwen-14b
TIER_CREATIVE_MODEL=qwen-7b

# Chunking
CHUNKING_STRATEGY=semantic   # or "recursive"
CHUNKING_THRESHOLD=8000      # Token threshold to trigger chunking
```

## Usage

### Basic Usage

```python
from inference import init, process, classify

# Initialize (optional - auto-initializes on first call)
init()

# Full pipeline: classify + route
result = process("What is the capital of France?")
print(result.classification.complexity)  # "simple"
print(result.target_model)               # "qwen-0.5b"

# Classification only
classification = classify("Analyze the economic implications of...")
print(classification.complexity)  # "complex"
print(classification.confidence)  # 0.92
```

### Quick Classification (No Model Call)

```python
# Use heuristics for fast classification
result = process("Hello!", use_quick_classify=True)
```

### Custom Workflows

```python
from inference import WorkflowRegistry

@WorkflowRegistry.register("my_workflow", description="Custom logic")
def my_workflow(prompt: str, config: dict) -> dict:
    # Your custom processing logic
    return {"result": "..."}

# Use the custom workflow
orchestrator = get_orchestrator()
result = orchestrator.process_with_custom_workflow(prompt, "my_workflow")
```

## Complexity Levels

| Level | Description | Typical Use Case |
|-------|-------------|------------------|
| `simple` | Fact retrieval, basic QA | "What is 2+2?" |
| `medium` | General conversation | "Explain photosynthesis" |
| `complex` | Multi-step reasoning | "Analyze pros and cons of..." |
| `long_context` | Extended context | Documents, long conversations |
| `code` | Programming tasks | "Write a function that..." |
| `creative` | Creative writing | "Write a poem about..." |

## Project Structure

```
inference/
├── __init__.py          # Package exports
├── api.py               # Public API functions
├── config.yaml          # Workflow definitions
├── requirements.txt     # Dependencies
├── core/
│   ├── config_loader.py     # Configuration loading
│   ├── orchestrator.py      # Main workflow coordinator
│   └── workflow_registry.py # Custom workflow registration
├── models/
│   ├── classification.py    # Pydantic models
│   └── workflow.py          # Workflow config models
├── services/
│   ├── classifier.py        # Instructor-based classifier
│   ├── router.py            # Tier-based routing
│   └── chunker.py           # LlamaIndex chunking
└── workflows/
    └── examples.py          # Example custom workflows
```

## API Reference

| Function | Description |
|----------|-------------|
| `init(config_path, env_path)` | Initialize the workflow |
| `process(prompt, workflow, use_quick_classify)` | Full pipeline |
| `classify(prompt, use_quick)` | Classification only |
| `route(classification)` | Route a classification |
| `chunk(text)` | Chunk long text |
| `should_chunk(text)` | Check if chunking needed |
| `list_workflows()` | List available workflows |
| `reload_config()` | Reload configuration |

## Dependencies

- **pydantic**: Structured output models
- **instructor**: LLM structured output
- **openai**: API client for Llama.cpp endpoint
- **llama-index**: Semantic/recursive chunking
- **python-dotenv**: Environment configuration

## License

MIT
