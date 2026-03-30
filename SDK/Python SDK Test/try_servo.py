"""
Try the Servo SDK - edit the keys and prompts below, then run.

Setup:
    1. Sign up at the Servo dashboard and create an API key.
    2. Get a Google AI Studio key at aistudio.google.com (free tier available).
    3. Make sure the Servo classifier is running locally on port 8080.
    4. Install the SDK:
           pip install -e "../Python SDK[google]"
    5. Run:
           python try_servo.py
"""
import os
from pathlib import Path

from servo_sdk import Servo


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
# Keys - stored in the repo root .env file or your shell environment
# ---------------------------------------------------------------------------

SERVO_API_KEY = os.environ.get("SERVO_API_KEY", "")
GOOGLE_API_KEY = os.environ.get("GOOGLE_AI_STUDIO_API_KEY", "")
CLASSIFIER_URL = os.environ.get("CLASSIFIER_ENDPOINT", "http://localhost:8080")
SERVO_ENDPOINT = os.environ.get("SERVO_ENDPOINT", "http://localhost:3000")

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
]

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

for label, prompt in PROMPTS:
    print(f"\n[{label.upper()}] Prompt: {prompt}\n{'='*60}")

    classified = client.decompose_and_classify(prompt)
    print(f"Subtasks ({len(classified.subtasks)}):")
    for st in classified.subtasks:
        depends = f" -> depends_on {st.depends_on}" if st.depends_on else ""
        print(f"  [{st.complexity_id}] {st.id}: {st.text}{depends}")

    contextualized, db = client.embed_and_contextualize(classified)
    try:
        result = client.route_and_execute(contextualized, db, original_prompt=prompt)

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
