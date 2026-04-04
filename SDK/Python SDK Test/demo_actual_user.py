import os
from pathlib import Path

from dotenv import load_dotenv
from servo_sdk import Servo


load_dotenv(Path(__file__).resolve().parents[2] / ".env.local")

client = Servo(
    api_key=os.environ["SERVO_API_KEY"],
    classifier_url=os.environ["CLASSIFIER_ENDPOINT"],
    telemetry_mode="sync",
    provider_api_keys={"google": os.environ["GOOGLE_AI_STUDIO_API_KEY"]},
)

prompt = "I’m creating a task management app and want to know the main features users expect, a simple product description I could put on a landing page, and a sensible pricing structure for individuals and teams."
result = client.decompose_classify_embed_and_execute(prompt)

print("\nFinal response:\n")
print(result.final_response)
print(f"\nTotal cost: ${result.total_cost:.6f}")
print(f"Total savings: ${result.total_savings:.6f}")
