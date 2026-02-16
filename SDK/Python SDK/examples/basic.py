from servo_sdk import Servo


def main() -> None:
    client = Servo(
        api_key="ADAOWODWA",
        base_url="http://localhost:8000",
        default_user_id="default_user"
    )
    
    # Get categories
    categories = client.categories()
    print(f"Available categories: {[c.id for c in categories.categories]}\n")
    
    # Send a request
    result = client.send("Who was the first president of the United States?")
    
    print(f"Category: {result.classification.category_id}")
    print(f"Model: {result.target_model}")
    print(f"Confidence: {result.classification.confidence:.2f}")
    print(f"LLM Response: {result.llm_response}")


if __name__ == "__main__":
    main()
