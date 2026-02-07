"""Prompt classification service using Instructor with Qwen3-14B."""

import os
import instructor
from openai import OpenAI
from typing import Optional

from ..models.classification import ClassificationResult, ComplexityLevel


# System prompt for the classifier model
CLASSIFICATION_SYSTEM_PROMPT = """You are a prompt complexity classifier. Analyze the user's prompt and classify it into one of the following complexity levels:

1. **simple**: Fact retrieval, simple QA, greetings, basic questions with straightforward answers
2. **medium**: General conversation, moderate reasoning, summaries, explanations
3. **complex**: Multi-step reasoning, analysis, comparisons, detailed explanations, problem-solving
4. **long_context**: Prompts that reference or require processing large amounts of text/context
5. **code**: Code generation, debugging, code analysis, programming-related tasks
6. **creative**: Creative writing, storytelling, poetry, artistic content generation

Consider the following when classifying:
- Token/length requirements
- Reasoning depth needed
- Domain specificity
- Whether the task requires multi-step thinking

Provide a confidence score between 0 and 1 for your classification.
Always suggest the appropriate model tier based on your classification."""


class PromptClassifier:
    """Classifier service for determining prompt complexity."""
    
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
        self.model = os.getenv(
            "CLASSIFIER_MODEL",
            config.get("model", "qwen3-14b") if config else "qwen3-14b"
        )
        self.temperature = float(os.getenv(
            "CLASSIFIER_TEMPERATURE",
            config.get("temperature", 0.1) if config else 0.1
        ))
        
        # Initialize Instructor-wrapped OpenAI client
        self.client = instructor.from_openai(
            OpenAI(base_url=self.endpoint, api_key="not-needed"),
            mode=instructor.Mode.JSON
        )
    
    def classify(self, prompt: str) -> ClassificationResult:
        """
        Classify the complexity of a prompt.
        
        Args:
            prompt: The user prompt to classify.
            
        Returns:
            ClassificationResult with complexity level and metadata.
        """
        response = self.client.chat.completions.create(
            model=self.model,
            response_model=ClassificationResult,
            temperature=self.temperature,
            messages=[
                {"role": "system", "content": CLASSIFICATION_SYSTEM_PROMPT},
                {"role": "user", "content": f"Classify this prompt:\n\n{prompt}"}
            ]
        )
        return response
    
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
        
        # Check for long context
        if token_estimate > 2000:
            return ComplexityLevel.LONG_CONTEXT
        
        # Check for code-related keywords
        code_keywords = ["code", "function", "class", "debug", "error", "programming", 
                        "python", "javascript", "java", "```", "def ", "import "]
        if any(kw in prompt_lower for kw in code_keywords):
            return ComplexityLevel.CODE
        
        # Check for creative keywords
        creative_keywords = ["write a story", "write a poem", "creative", "imagine", 
                           "fiction", "narrative", "once upon"]
        if any(kw in prompt_lower for kw in creative_keywords):
            return ComplexityLevel.CREATIVE
        
        # Check for simple queries
        simple_patterns = ["what is", "who is", "when did", "where is", "define", 
                          "hello", "hi", "thanks", "thank you"]
        if any(prompt_lower.startswith(p) or prompt_lower == p for p in simple_patterns):
            return ComplexityLevel.SIMPLE
        
        # Check for complex reasoning indicators
        complex_keywords = ["analyze", "compare", "explain why", "what are the implications",
                           "pros and cons", "evaluate", "critique", "in-depth"]
        if any(kw in prompt_lower for kw in complex_keywords):
            return ComplexityLevel.COMPLEX
        
        # Default to medium
        return ComplexityLevel.MEDIUM
