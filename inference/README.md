# Right-Sizing Inference Router

## Overview

A classification and routing backend that now supports user-specific category definitions.
For MVP, user profiles are hardcoded in `inference/configs/user_classification_profiles.py`.

## Key Features

- Per-user classification categories (`user_id` based).
- Classifier constrained to only allowed categories for the user.
- Category metadata includes provider, endpoint, and model id.
- Routing sends original prompt to Google AI Studio via OpenAI-compatible API.

## Prerequisites

- Python 3.10+
- Local OpenAI-compatible endpoint for classifier model (default `http://localhost:8080/v1`)
- Google AI Studio API key

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

GOOGLE_AI_STUDIO_API_KEY=your_google_ai_studio_key

SERVER_HOST=0.0.0.0
SERVER_PORT=8000

CHUNKING_STRATEGY=semantic
CHUNKING_THRESHOLD=8000
CHUNKING_MAX_SIZE=4096
CHUNKING_OVERLAP=200
```

## Hardcoded User Category Profiles (MVP Placeholder)

Profiles live in:
- `inference/configs/user_classification_profiles.py`

Default seeded categories:
- `simple` -> Google Gemma 27B (`gemma-3-27b-it`)
- `complex` -> Gemini 2.5 Flash (`gemini-2.5-flash`)

## Run

```powershell
uvicorn inference.server:app --host 0.0.0.0 --port 8000 --reload
```

Interactive API docs:
- Swagger UI: `http://localhost:8000/docs`
- OpenAPI schema: `http://localhost:8000/openapi.json`

## API

Base URL (local): `http://localhost:8000`

### `GET /health`

Response type:

```json
{
  "status": "string"
}
```

Example response:

```json
{
  "status": "ok"
}
```

### `POST /classify`

Request:

```json
{
  "user_id": "default_user",
  "prompt": "Explain the tradeoffs between columnar and row storage",
  "use_quick": false
}
```

Response type (`ClassificationResult`):

```json
{
  "category_id": "string",
  "category_name": "string",
  "reasoning": "string",
  "requires_chunking": false,
  "confidence": 0.0
}
```

Example response:

```json
{
  "category_id": "complex",
  "category_name": "Complex",
  "reasoning": "The prompt asks for comparative analysis with tradeoffs.",
  "requires_chunking": false,
  "confidence": 0.94
}
```

### `POST /process`

Request:

```json
{
  "user_id": "default_user",
  "prompt": "Who was the first president of the United States?"
}
```

Response type (`ProcessingResult`):

```json
{
  "classification": {
    "category_id": "string",
    "category_name": "string",
    "reasoning": "string",
    "requires_chunking": false,
    "confidence": 0.0
  },
  "target_model": "string",
  "selected_category": {
    "id": "string",
    "name": "string",
    "description": "string",
    "provider": "string",
    "endpoint": "string",
    "model_id": "string",
    "request_defaults": {}
  },
  "llm_response": "string or null",
  "chunks": [
    "string"
  ],
  "chunk_metadata": null,
  "requires_aggregation": false
}
```

Example response:

```json
{
  "classification": {
    "category_id": "simple",
    "category_name": "Simple",
    "reasoning": "Single factual lookup.",
    "requires_chunking": false,
    "confidence": 0.93
  },
  "target_model": "gemma-3-27b-it",
  "selected_category": {
    "id": "simple",
    "name": "Simple",
    "description": "Basic factual lookup or lightweight response generation.",
    "provider": "google_ai_studio",
    "endpoint": "https://generativelanguage.googleapis.com/v1beta/openai/",
    "model_id": "gemma-3-27b-it",
    "request_defaults": {
      "temperature": 0.2
    }
  },
  "llm_response": "George Washington was the first president of the United States.",
  "chunks": null,
  "chunk_metadata": null,
  "requires_aggregation": false
}
```

### `POST /route`

Request:

```json
{
  "user_id": "default_user",
  "classification": {
    "category_id": "simple",
    "category_name": "Simple",
    "reasoning": "Single factual lookup.",
    "requires_chunking": false,
    "confidence": 0.95
  }
}
```

Response type:

```json
{
  "target_model": "string"
}
```

Example response:

```json
{
  "target_model": "gemma-3-27b-it"
}
```

### `GET /tiers?user_id=default_user`

Compatibility endpoint: returns `{ category_id: model_id }`.

Response type:

```json
{
  "tiers": {
    "simple": "gemma-3-27b-it",
    "complex": "gemini-2.5-flash"
  }
}
```

### `GET /categories?user_id=default_user`

Returns full category metadata for the specified user profile.

Response type:

```json
{
  "user_id": "string",
  "default_category_id": "string",
  "categories": [
    {
      "id": "string",
      "name": "string",
      "description": "string",
      "provider": "string",
      "endpoint": "string",
      "model_id": "string",
      "request_defaults": {}
    }
  ]
}
```

Example response:

```json
{
  "user_id": "default_user",
  "default_category_id": "simple",
  "categories": [
    {
      "id": "simple",
      "name": "Simple",
      "description": "Use for direct, bounded tasks: factual Q&A, concise explanations, and routine coding work (for example implementing a single Python function, small bug fixes, or straightforward refactors). Prefer this category whenever the request can be fully handled without deep multi-step analysis.",
      "provider": "google_ai_studio",
      "endpoint": "https://generativelanguage.googleapis.com/v1beta/openai/",
      "model_id": "gemma-3-27b-it",
      "request_defaults": {
        "temperature": 0.2
      }
    },
    {
      "id": "complex",
      "name": "Complex",
      "description": "Use only when the task genuinely requires deeper reasoning: broad system design, non-trivial architecture or migration plans, advanced debugging across multiple interacting components, or nuanced tradeoff analysis. Do not use for routine single-file or single-function coding tasks.",
      "provider": "google_ai_studio",
      "endpoint": "https://generativelanguage.googleapis.com/v1beta/openai/",
      "model_id": "gemini-2.5-flash",
      "request_defaults": {
        "temperature": 0.2
      }
    }
  ]
}
```

## Project Structure

```text
inference/
├── configs/
│   └── user_classification_profiles.py
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
    ├── provider_google_ai_studio.py
    └── chunker.py
```
