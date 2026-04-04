from servo_sdk import Servo


def main() -> None:
    client = Servo(
        api_key="your-servo-api-key",
        classifier_url="http://localhost:8080",
        provider_api_keys={"google": "your-google-ai-studio-key"},
    )

    result = client.decompose_classify_embed_and_execute(
        "Explain what machine learning is and give two real-world examples."
    )

    print(result.final_response)
    print(f"\nTotal cost: ${result.total_cost:.6f}")
    print(f"Total savings: ${result.total_savings:.6f}")


if __name__ == "__main__":
    main()
