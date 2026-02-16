# Python SDK Test

Test suite for the Servo Python SDK.

## Setup

```bash
# Install the SDK in development mode
pip install -e "../Python SDK"
```

## Running Tests

Make sure the Servo backend is running on `http://localhost:8000`:

```bash
# From the Servo folder
uvicorn inference.server:app --host 0.0.0.0 --port 8000 --reload
```

Then run the tests:

```bash
# Basic test
python test_basic.py

# Conversation test
python test_conversation.py
```

## Test Files

- **test_basic.py** - Basic SDK functionality (health, categories, classify, route, send)
- **test_conversation.py** - Conversation context management

## Expected Output

The tests should output:
- Health check status
- Available categories
- Classification results with category_id and category_name
- Target model routing
- LLM responses
- Confidence scores

## Requirements

- Python 3.10+
- Servo backend running
- Python SDK installed
