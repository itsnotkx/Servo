"""
Minimal Servo SDK demo for end users.

This example shows the intended public flow:
  1. Install the SDK
  2. Set your API keys
  3. Pass a prompt to Servo
  4. Let the SDK handle routing, execution, and telemetry automatically
"""
from __future__ import annotations

import os

from servo_sdk import Servo


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def main() -> None:
    client = Servo(
        api_key=require_env("SERVO_API_KEY"),
        classifier_url=os.environ.get("CLASSIFIER_ENDPOINT", "http://localhost:8080"),
        provider_api_keys={"google": require_env("GOOGLE_AI_STUDIO_API_KEY")},
    )

    prompt = input("Enter your prompt for Servo: ").strip()
    if not prompt:
        raise RuntimeError("Prompt cannot be empty.")

    result = client.decompose_classify_embed_and_execute(prompt)

    print("\nFinal response")
    print("=" * 60)
    print(result.final_response)
    print("=" * 60)
    print(f"Total cost: ${result.total_cost:.6f}")
    print(f"Total savings: ${result.total_savings:.6f}")


if __name__ == "__main__":
    main()
