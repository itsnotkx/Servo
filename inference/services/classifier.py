"""Prompt classification service using Outlines with Qwen3-14B."""

import os
import outlines
from openai import OpenAI
from typing import Optional

from ..models.classification import ClassificationResult, ComplexityLevel


class PromptClassifier:
    """Classifier service for determining prompt complexity using Outlines."""

    def __init__(self, config: Optional[dict] = None):
        """
        Initialize the classifier.

        Args:
            config: Optional configuration dict. If not provided,
                    loads from environment variables.
        """
        self.endpoint = os.getenv(
            "CLASSIFIER_ENDPOINT",
            config.get("endpoint", "http://localhost:8080/v1") if config else "http://localhost:8080/v1"
        )
        self.model_name = os.getenv(
            "CLASSIFIER_MODEL",
            config.get("model", "qwen3-14b") if config else "qwen3-14b"
        )
        self.temperature = float(os.getenv(
            "CLASSIFIER_TEMPERATURE",
            config.get("temperature", 0.1) if config else 0.1
        ))

        # Initialize OpenAI client and Outlines wrapper
        # outlines.from_openai() wraps the client to enforce structured output
        self.client = OpenAI(base_url=self.endpoint, api_key="not-needed")
        self.model = outlines.from_openai(self.client, self.model_name)

    def classify(self, prompt: str) -> ClassificationResult:
        """
        Classify the complexity of a prompt.

        Args:
            prompt: The user prompt to classify.

        Returns:
            ClassificationResult with complexity level and metadata.
        """
        # Outlines takes the prompt string and the Pydantic model
        # It guarantees the output matches the model schema
        result = self.model(prompt, ClassificationResult)

        # If result is a string (JSON), parse it into the Pydantic model
        if isinstance(result, str):
            return ClassificationResult.model_validate_json(result)

        return result

    def quick_classify(self, prompt: str) -> ComplexityLevel:
        """
        Perform a quick heuristic classification without calling the model.
        Useful for obvious cases or when the model is unavailable.

        Args:
            prompt: The user prompt to classify.

        Returns:
            ComplexityLevel based on heuristics.
        """
        prompt_lower = prompt.lower().strip()
        token_estimate = len(prompt) // 4  # Rough token estimate

        # Very short social/factual prompts are usually lightweight.
        simple_patterns = [
            "what is", "who is", "when did", "where is", "define",
            "hello", "hi", "thanks", "thank you"
        ]
        if any(prompt_lower.startswith(p) or prompt_lower == p for p in simple_patterns):
            return ComplexityLevel.SIMPLE

        # Strong indicators for deep reasoning or specialist tasks.
        complex_keywords = [
            "analyze", "compare", "explain why", "implications",
            "pros and cons", "evaluate", "critique", "in-depth",
            "step by step", "design", "architecture", "debug",
            "optimize", "algorithm", "prove", "tradeoff"
        ]
        if token_estimate > 2000 or any(kw in prompt_lower for kw in complex_keywords):
            return ComplexityLevel.COMPLEX

        # Default bucket for requests requiring some reasoning but not heavy analysis.
        return ComplexityLevel.THINKING
