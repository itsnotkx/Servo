"""Prompt classification service using Outlines and Llama-cpp-python."""

import os
import outlines
from typing import Optional, Dict, Any, cast

from llama_cpp import Llama

from ..models.classification import ClassificationResult, ComplexityLevel


# System prompt for the classifier model
CLASSIFICATION_SYSTEM_PROMPT = """You are a prompt complexity classifier. Analyze the user's prompt and classify it into one of the following complexity levels:

1. **simple**: Fact retrieval, simple QA, greetings, basic questions with straightforward answers
2. **medium**: General conversation, moderate reasoning, summaries, explanations
3. **complex**: Multi-step reasoning, analysis, comparisons, detailed explanations, problem-solving
4. **long_context**: Prompts that reference or require processing large amounts of text/context
5. **code**: Code generation, debugging, code analysis, programming-related tasks
6. **creative**: Creative writing, storytelling, poetry, artistic content generation

You must return a valid JSON object matching the schema.
Required fields:
- "complexity": One of the levels above (e.g., "simple", "medium").
- "reasoning": A brief explanation for the classification.
- "requires_chunking": Boolean indicating if the input is too long.
- "suggested_model_tier": The recommended model tier (e.g., "simple", "complex").
- "confidence": A float score between 0.0 and 1.0.
"""


class PromptClassifier:
    """Classifier service for determining prompt complexity."""
    
    def __init__(self, config: Optional[dict] = None):
        """
        Initialize the classifier.
        
        Args:
            config: Optional configuration dict. If not provided, 
                    loads from environment variables.
        """
        config = config or {}
        
        model_path = os.getenv(
            "MODEL_PATH",
            config.get("model_path")
        )
        
        if not model_path:
            raise ValueError("MODEL_PATH environment variable or config is required.")
            
        n_gpu_layers = int(os.getenv(
            "N_GPU_LAYERS",
            config.get("n_gpu_layers", -1) # Default to all layers
        ))
        
        n_ctx = int(os.getenv(
            "N_CTX",
            config.get("n_ctx", 2048)
        ))
        
        n_batch = int(os.getenv(
            "N_BATCH",
            config.get("n_batch", 512)
        ))

        self.temperature = float(os.getenv(
            "CLASSIFIER_TEMPERATURE",
            config.get("temperature", 0.1)
        ))
        
        # Initialize Llama-cpp model via Outlines
        llm = Llama(
            model_path=model_path,
            n_gpu_layers=n_gpu_layers,
            n_ctx=n_ctx,
            n_batch=n_batch,
            verbose=False
        )
        self.model = outlines.models.LlamaCpp(llm)
    
    def classify(self, prompt: str) -> ClassificationResult:
        """
        Classify the complexity of a prompt.
        
        Args:
            prompt: The user prompt to classify.
            
        Returns:
            ClassificationResult with complexity level and metadata.
        """
        # Construct the prompt
        full_prompt = f"{CLASSIFICATION_SYSTEM_PROMPT}\n\nUser Prompt: {prompt}\n\nClassification:"
        
        # Generate structured output
        # New interface: model(prompt, schema)
        result = self.model(
            full_prompt,
            ClassificationResult
        )
        
        return cast(ClassificationResult, result)
    
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
