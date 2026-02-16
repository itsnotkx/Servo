"""Test conversation context management with the Servo Python SDK."""

import sys
from pathlib import Path

# Add the Python SDK to the path
sdk_path = Path(__file__).parent.parent / "Python SDK"
sys.path.insert(0, str(sdk_path))

from servo_sdk import Servo
from servo_sdk.context import Conversation


def main():
    """Test conversation features."""
    client = Servo(
        api_key="ADAWODWA",
        base_url="http://localhost:8000",
        default_user_id="default_user"
    )

    try:
        print("Testing Servo SDK with conversation context...")
        
        # Create a conversation with system prompt
        conv = Conversation(system_prompt="You are a helpful math tutor.")
        conv.add_user("What is 5 + 3?")
        conv.add_assistant("5 + 3 equals 8.")
        
        # Send with conversation context
        result = client.send(
            "What about 10 + 7?",
            conversation=conv,
            use_quick_classify=False
        )
        
        print("\nResult with conversation context:")
        print(f"- Category: {result.classification.category_id}")
        print(f"- Model: {result.target_model}")
        print(f"- LLM Response: {result.llm_response}")
        
        # Test with built-in conversation manager
        client_conv = client.with_conversation()
        client_conv.add_user("Hello!")
        client_conv.add_assistant("Hi there! How can I help you today?")
        
        result2 = client.send("Tell me about Python programming.")
        print("\nResult with client conversation:")
        print(f"- Category: {result2.classification.category_id}")
        print(f"- Response: {result2.llm_response}")
        
    except Exception as error:
        print(f"Error: {error}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
