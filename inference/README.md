# Right-Sizing Inference Router

## Overview

A classification and routing system designed to optimize LLM inference cost and latency.
It routes prompts to one of three model categories: `simple`, `thinking`, or `complex`.

## Key Features

- Smart routing to right-sized models.
- FastAPI backend in `inference/server.py`.
- Structured output with `outlines`.
- Hybrid classification:
  - Quick mode: heuristic classification.
  - Model mode: classifier model with schema-constrained output.
- Configurable model tiers through `.env.local`.

## Prerequisites

- Python 3.10+
- Llama.cpp server (or any OpenAI-compatible local endpoint)
- Classifier model weights

## Installation

```bash
pip install -r inference/requirements.txt
```

## Configuration

Create `.env.local` in the project root.

```ini
CLASSIFIER_ENDPOINT=http://localhost:8080/v1
CLASSIFIER_MODEL=qwen3-14b
CLASSIFIER_TEMPERATURE=0.1

SERVER_HOST=0.0.0.0
SERVER_PORT=8000

TIER_SIMPLE_MODEL=qwen-1.5b
TIER_THINKING_MODEL=qwen-7b
TIER_COMPLEX_MODEL=qwen-72b

CHUNKING_STRATEGY=semantic
CHUNKING_THRESHOLD=8000
CHUNKING_MAX_SIZE=4096
CHUNKING_OVERLAP=200
```

## Run

```powershell
uvicorn inference.server:app --host 0.0.0.0 --port 8000 --reload
```

## API

### `POST /classify`

Request:

```json
{
  "prompt": "Explain the tradeoffs between columnar and row storage",
  "use_quick": false
}
```

Response:

```json
{
  "complexity": "complex",
  "reasoning": "The prompt asks for comparative analysis with tradeoffs.",
  "requires_chunking": false,
  "suggested_model_tier": "complex",
  "confidence": 0.94
}
```

### `POST /process`

Request:

```json
{
  "prompt": "Who was the first president of the United States?"
}
```

Response:

```json
{
  "classification": {
    "complexity": "simple",
    "reasoning": "Single factual lookup.",
    "requires_chunking": false,
    "suggested_model_tier": "simple",
    "confidence": 0.93
  },
  "target_model": "qwen-1.5b",
  "chunks": null,
  "chunk_metadata": null,
  "requires_aggregation": false
}
```

### `GET /tiers`

Returns currently configured models for the three tiers.

## Project Structure

```text
inference/
├── server.py
├── config.yaml
├── core/
│   ├── config_loader.py
│   └── orchestrator.py
├── models/
│   └── classification.py
└── services/
    ├── classifier.py
    ├── router.py
    └── chunker.py
```
