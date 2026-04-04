# Python SDK Test

Quick-start folder for trying the Servo Python SDK locally.

## Setup

```bash
cd "SDK/Python SDK Test"
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e "../Python SDK[google]"
```

## Run

Make sure the classifier (llama-server) is running on port 8080, then:

```bash
python try_servo.py
```

You can override defaults with environment variables:

```bash
export GOOGLE_AI_STUDIO_API_KEY="your-key"
export CLASSIFIER_ENDPOINT="http://100.74.1.39:8080"   # remote machine via Tailscale
python try_servo.py
```
