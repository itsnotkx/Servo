# Servo Python SDK

Python SDK for the Servo backend (routing/classification).

## Features

✅ **Simple end-user API** - Initialize, prompt, receive  
✅ **Full type hints** - Type-safe with dataclasses  
✅ **Conversation management** - Built-in chat history handling  
✅ **Modern Python** - Python 3.10+ with type annotations  
✅ **Minimal dependencies** - Uses standard library HTTP client

## Installation

```bash
pip install servo-sdk
```

Or install in development mode:

```bash
pip install -e .
```

## Quick Start

```python
from servo_sdk import Servo

client = Servo(
    api_key="your-api-key",
    classifier_url="http://localhost:8080",
    telemetry_mode="sync",
    provider_api_keys={"google": "your-google-ai-studio-key"},
)

result = client.decompose_classify_embed_and_execute(
    "Who was the first president of the United States?"
)

print(result.final_response)
print(result.total_cost)
print(result.total_savings)
```

## Usage

### Basic Usage

```python
from servo_sdk import Servo

client = Servo(
    api_key="your-servo-api-key",
    classifier_url="http://localhost:8080",
    telemetry_mode="sync",
    provider_api_keys={"google": "your-google-ai-studio-key"},
)

result = client.decompose_classify_embed_and_execute("What is machine learning?")
print(result.final_response)
print(result.total_cost)
print(result.total_savings)
```

### Demo Recording Flow

```bash
cd "SDK/Python SDK"
pip install -e ".[google]"
python examples/demo_user_flow.py
```

When the script prompts for input, the user only enters their prompt. Servo handles
decomposition, routing, execution, and telemetry automatically inside the SDK.

### With Conversation Context

```python
from servo_sdk import Servo
from servo_sdk.context import Conversation

client = Servo(api_key="your-key")

# Create a conversation with system prompt
conversation = Conversation(system_prompt="You are a helpful AI assistant.")
conversation.add_user("Hello!")
conversation.add_assistant("Hi there!")

# Send with conversation context
result = client.send("What did we just discuss?", conversation=conversation)
```

### Step-by-Step Processing

```python
# Step 1: Classify the prompt
classification = client.classify(
    "Explain quantum computing",
    user_id=None,        # optional, uses default_user_id
    use_quick=False      # default: False
)

print(classification.category_id)         # e.g., 'simple' or 'complex'
print(classification.category_name)       # e.g., 'Simple' or 'Complex'
print(classification.confidence)          # 0.0 - 1.0
print(classification.requires_chunking)   # boolean

# Step 2: Route to appropriate model
routing = client.route(classification)
print(routing.target_model)  # e.g., 'gemini-2.5-flash'
```

### Health Check & Tiers

```python
# Check backend health
health = client.health()
print(health)

# Get available model tiers
tiers = client.tiers()
print(tiers.tiers)  # {'simple': 'gemini-2.5-flash-lite', 'complex': 'gemini-2.5-flash'}

# Get available categories with full metadata
categories = client.categories()
print(categories.user_id)             # 'default_user'
print(categories.default_category_id) # 'simple'
print(categories.categories)          # list of ClassificationCategory
```

## API Reference

See the full type definitions in `servo_sdk/types.py` and client methods in `servo_sdk/client.py`.

### Key Types

- `ClassificationResult` - Result from classifying a prompt
- `ClassificationCategory` - Category metadata with provider and model info
- `CategoriesResponse` - User-specific categories configuration
- `ProcessingResult` - Complete result including classification, routing, and LLM response
- `TiersResponse` - Mapping of category IDs to model IDs

## Requirements

- **Python 3.10+** (for union type syntax)

## Development

```bash
# Install in development mode
pip install -e .

# Run tests
pytest
```
