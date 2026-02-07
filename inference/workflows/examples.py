"""Example custom workflows demonstrating the registry pattern."""

from ..core.workflow_registry import WorkflowRegistry
from ..services.classifier import PromptClassifier
from ..services.router import LLMRouter
from ..models.classification import ClassificationResult, ComplexityLevel


@WorkflowRegistry.register(
    name="code_focused",
    description="Optimized workflow for code-related prompts",
    version="1.0.0"
)
def code_focused_workflow(prompt: str, config: dict) -> dict:
    """
    A workflow optimized for code-related prompts.
    
    Always routes to the code tier regardless of classification.
    """
    classifier = PromptClassifier(config.get("classifier", {}))
    router = LLMRouter(config.get("routing", {}))
    
    # Classify for metadata, but override routing
    classification = classifier.classify(prompt)
    
    # Force code tier
    target_model = router.get_model_for_tier("code")
    
    return {
        "classification": classification.model_dump(),
        "target_model": target_model,
        "workflow_override": "code_focused",
    }


@WorkflowRegistry.register(
    name="quick_only",
    description="Fast heuristic-only classification without model calls",
    version="1.0.0"
)
def quick_classification_workflow(prompt: str, config: dict) -> dict:
    """
    A fast workflow that uses only heuristic classification.
    
    No model calls - useful for latency-sensitive applications.
    """
    classifier = PromptClassifier(config.get("classifier", {}))
    router = LLMRouter(config.get("routing", {}))
    
    # Use quick heuristic classification
    complexity = classifier.quick_classify(prompt)
    
    classification = ClassificationResult(
        complexity=complexity,
        reasoning="Heuristic-based quick classification",
        requires_chunking=False,
        suggested_model_tier=complexity.value,
        confidence=0.7,
    )
    
    target_model = router.route(classification)
    
    return {
        "classification": classification.model_dump(),
        "target_model": target_model,
        "workflow_override": "quick_only",
    }


@WorkflowRegistry.register(
    name="force_complex",
    description="Always routes to the complex tier for high-quality responses",
    version="1.0.0"
)
def force_complex_workflow(prompt: str, config: dict) -> dict:
    """
    Forces all prompts to use the complex tier.
    
    Useful when quality is more important than efficiency.
    """
    router = LLMRouter(config.get("routing", {}))
    
    classification = ClassificationResult(
        complexity=ComplexityLevel.COMPLEX,
        reasoning="Forced to complex tier by workflow",
        requires_chunking=False,
        suggested_model_tier="complex",
        confidence=1.0,
    )
    
    target_model = router.get_model_for_tier("complex")
    
    return {
        "classification": classification.model_dump(),
        "target_model": target_model,
        "workflow_override": "force_complex",
    }
