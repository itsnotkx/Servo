"""
Try the Servo SDK — edit the PROMPT below and run!

Setup:
    pip install -e "../Python SDK[google]"

Usage:
    python try_servo.py
"""
import os
import threading

from servo_sdk import Servo, RoutingCategory
from servo_sdk.client import ContextDB
from servo_sdk.types import CachedConfig, RoutingConfig

# ---------------------------------------------------------------------------
# Config — change these or set env vars
# ---------------------------------------------------------------------------

GOOGLE_API_KEY = os.environ.get("GOOGLE_AI_STUDIO_API_KEY", "YOUR_KEY_HERE")
CLASSIFIER_URL = os.environ.get("CLASSIFIER_ENDPOINT", "http://localhost:8080")

CATEGORIES = [
    RoutingCategory(id="simple",  name="Simple",  description="Straightforward, no reasoning",  model="gemini-2.5-flash-lite"),
    RoutingCategory(id="complex", name="Complex", description="Multi-step reasoning required",   model="gemini-3.1-flash-lite-preview"),
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
