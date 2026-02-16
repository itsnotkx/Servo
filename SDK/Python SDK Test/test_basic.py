"""Basic test for the Servo Python SDK."""

import sys
from pathlib import Path

# Add the Python SDK to the path
sdk_path = Path(__file__).parent.parent / "Python SDK"
sys.path.insert(0, str(sdk_path))

from servo_sdk import Servo


def main():
    """Test the Servo SDK with the backend."""
    client = Servo(
        api_key="ADAWODWA",
        base_url="http://localhost:8000",
        default_user_id="default_user"
    )

    try:
        print("Testing Servo SDK...")
        
        # Test health endpoint
        health = client.health()
        print(f"Health check: {health}")
        
        # Test categories
        categories = client.categories()
        print(f"\nAvailable categories: {[c.id for c in categories.categories]}")
        print(f"Default category: {categories.default_category_id}")
        
        # Test tiers
        tiers = client.tiers()
        print(f"\nTiers mapping: {tiers.tiers}")
        
        # Test send
        result = client.send("What is 2 + 2?")
        print("\nProcessing result:")
        print(f"- Category ID: {result.classification.category_id}")
        print(f"- Category Name: {result.classification.category_name}")
        print(f"- Reasoning: {result.classification.reasoning}")
        print(f"- Target Model: {result.target_model}")
        print(f"- Confidence: {result.classification.confidence:.2f}")
        print(f"- LLM Response: {result.llm_response}")
        
        # Test classify separately
        classification = client.classify("Explain quantum mechanics in detail", use_quick=False)
        print("\nClassification result:")
        print(f"- Category: {classification.category_id}")
        print(f"- Confidence: {classification.confidence:.2f}")
        
        # Test route
        routing = client.route(classification)
        print(f"- Routed to model: {routing.target_model}")
        
    except Exception as error:
        print(f"Error: {error}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
