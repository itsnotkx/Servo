"""
Try the Servo SDK — edit the PROMPT below and run!

Setup:
    pip install -e "../Python SDK[google]"

Usage:
    python try_servo.py
"""
import os
<<<<<<< HEAD
import threading
=======
from pathlib import Path
>>>>>>> 6b44263 (Move SDK test keys to env and expand try_servo prompts)

from servo_sdk import Servo, RoutingCategory
from servo_sdk.client import ContextDB
from servo_sdk.types import CachedConfig, RoutingConfig


def load_repo_env() -> None:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_repo_env()

# ---------------------------------------------------------------------------
<<<<<<< HEAD
# Config — change these or set env vars
# ---------------------------------------------------------------------------

GOOGLE_API_KEY = os.environ.get("GOOGLE_AI_STUDIO_API_KEY", "YOUR_KEY_HERE")
=======
# Keys - stored in the repo root .env file or your shell environment
# ---------------------------------------------------------------------------

SERVO_API_KEY = os.environ.get("SERVO_API_KEY", "")
GOOGLE_API_KEY = os.environ.get("GOOGLE_AI_STUDIO_API_KEY", "")
>>>>>>> 6b44263 (Move SDK test keys to env and expand try_servo prompts)
CLASSIFIER_URL = os.environ.get("CLASSIFIER_ENDPOINT", "http://localhost:8080")

<<<<<<< HEAD
CATEGORIES = [
    RoutingCategory(id="simple",  name="Simple",  description="Straightforward, no reasoning",  model="gemini-2.5-flash-lite"),
    RoutingCategory(id="complex", name="Complex", description="Multi-step reasoning required",   model="gemini-3.1-flash-lite-preview"),
=======
if not SERVO_API_KEY or not GOOGLE_API_KEY:
    raise RuntimeError("Set SERVO_API_KEY and GOOGLE_AI_STUDIO_API_KEY in the repo root .env file.")

# ---------------------------------------------------------------------------
# Init client - validates your key and fetches your routing config
# ---------------------------------------------------------------------------

os.environ["SERVO_ENDPOINT"] = SERVO_ENDPOINT

client = Servo(
    api_key=SERVO_API_KEY,
    classifier_url=CLASSIFIER_URL,
    provider_api_keys={"google": GOOGLE_API_KEY},
)

# ---------------------------------------------------------------------------
# Test prompts
# ---------------------------------------------------------------------------

PROMPTS = [
    (
        "simple",
        "What is the capital of France, and what is it most famous for?",
    ),
    (
        "complex",
        (
            "Design a scalable microservices architecture for an e-commerce platform. "
            "Include service decomposition, inter-service communication patterns, "
            "a strategy for handling distributed transactions, and how you would "
            "approach fault tolerance and observability across services."
        ),
    ),
    (
        "mixed",
        (
            "What is the capital of Japan? "
            "What is machine learning? "
            "Then design and implement a neural network from scratch in Python (no ML libraries) "
            "that learns XOR, explaining backpropagation and the role of activation functions."
        ),
    ),
>>>>>>> 6b44263 (Move SDK test keys to env and expand try_servo prompts)
]
CONFIG = RoutingConfig(default_category_id="simple", categories=CATEGORIES)

# ---------------------------------------------------------------------------
# Build client (local mode — bypasses Servo backend)
# ---------------------------------------------------------------------------

original_post_init = Servo.__post_init__

def _bypass(self: Servo) -> None:
    self._classifier_url = CLASSIFIER_URL
    self._default_conversation = None
    self._embedding_fn_cache = None
    self._db_lock = threading.Lock()
    self._cached_config = CachedConfig(
        key_id="demo-key",
        user_id="demo-user",
        model="demo",
        tags=[],
        tiers={c.id: c.model for c in CATEGORIES},
        routing_config=CONFIG,
        model_pricing={
            "gemini-2.5-flash-lite": (0.10, 0.20),
            "gemini-3.1-flash-lite-preview": (0.10, 0.40),
        },
        baseline_model_id="gemini-3.1-flash-lite-preview",
    )

Servo.__post_init__ = _bypass
client = Servo(api_key="sk_demo", timeout_s=120.0)
Servo.__post_init__ = original_post_init

client.provider_api_keys["google"] = GOOGLE_API_KEY

# ---------------------------------------------------------------------------
# Your prompt — edit this!
# ---------------------------------------------------------------------------

PROMPT = "What is the capital of France and what is it famous for?"

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

print(f"\nPrompt: {PROMPT}\n{'='*60}")

classified = client.decompose_and_classify(PROMPT)
print(f"Subtasks ({len(classified.subtasks)}):")
for st in classified.subtasks:
    depends = f" -> depends_on {st.depends_on}" if st.depends_on else ""
    print(f"  [{st.complexity_id}] {st.id}: {st.text}{depends}")

contextualized, db = client.embed_and_contextualize(classified)
try:
    result = client.route_and_execute(contextualized, db, original_prompt=PROMPT)

    # Print RAG database contents
    rag_contents = db.get_all()
    print(f"\n{'='*60}\nRAG DATABASE ({len(rag_contents)} entries):\n{'='*60}")
    for sid, content in rag_contents.items():
        print(f"\n[ID: {sid}]\n{content[:500]}")
        if len(content) > 500:
            print(f"  ... ({len(content)} chars total)")
    print(f"\n{'='*60}")
finally:
    db.close()

print(f"\nExecution ({len(result.subtask_results)} subtasks):")
for r in result.subtask_results:
    ctx = " [context injected]" if r.depends_on else ""
    print(f"  [{r.complexity_id}] {r.subtask_id} -> {r.model}{ctx}")
    print(f"    tokens: in={r.input_tokens} out={r.output_tokens}  cost=${r.cost:.6f}  savings=${r.cost_savings:.6f}")

print(f"\ntotal_cost=${result.total_cost:.6f}  total_savings=${result.total_savings:.6f}")
print(f"\n{'='*60}\nFINAL RESPONSE:\n{'='*60}\n{result.final_response}\n{'='*60}")
