"""Public API for the right-sizing inference workflow."""

from typing import Optional, Dict, Any, List

from .core.orchestrator import WorkflowOrchestrator
from .core.workflow_registry import WorkflowRegistry
from .models.classification import (
    ClassificationResult,
    ComplexityLevel,
    ProcessingResult,
    ChunkMetadata,
)


# Global orchestrator instance (singleton)
_orchestrator: Optional[WorkflowOrchestrator] = None


def init(
    config_path: Optional[str] = None,
    env_path: Optional[str] = None
) -> WorkflowOrchestrator:
    """
    Initialize the right-sizing workflow.
    
    Args:
        config_path: Path to config.yaml. Defaults to inference/config.yaml.
        env_path: Path to .env.local. Defaults to project root .env.local.
        
    Returns:
        Initialized WorkflowOrchestrator instance.
    """
    global _orchestrator
    _orchestrator = WorkflowOrchestrator(config_path, env_path)
    return _orchestrator


def get_orchestrator() -> WorkflowOrchestrator:
    """
    Get the current orchestrator instance, initializing if needed.
    
    Returns:
        WorkflowOrchestrator instance.
    """
    global _orchestrator
    if _orchestrator is None:
        init()
    return _orchestrator


def process(
    prompt: str, 
    workflow: str = "default",
    use_quick_classify: bool = False
) -> ProcessingResult:
    """
    Process a prompt through the right-sizing workflow.
    
    Args:
        prompt: The user prompt to process.
        workflow: Name of the workflow to use.
        use_quick_classify: Use heuristic classification instead of model.
        
    Returns:
        ProcessingResult with classification, routing, and chunking info.
        
    Example:
        >>> from inference import process
        >>> result = process("What is 2+2?")
        >>> print(result.classification.complexity)
        simple
        >>> print(result.target_model)
        qwen-0.5b
    """
    orchestrator = get_orchestrator()
    return orchestrator.process(prompt, workflow, use_quick_classify)


def classify(
    prompt: str,
    use_quick: bool = False
) -> ClassificationResult:
    """
    Classify a prompt without routing.
    
    Args:
        prompt: The prompt to classify.
        use_quick: Use heuristic classification instead of model.
        
    Returns:
        ClassificationResult with complexity and metadata.
        
    Example:
        >>> from inference import classify
        >>> result = classify("Write a poem about the moon")
        >>> print(result.complexity)
        creative
    """
    orchestrator = get_orchestrator()
    return orchestrator.classify_only(prompt, use_quick)


def route(classification: ClassificationResult) -> str:
    """
    Route a classification result to the appropriate model.
    
    Args:
        classification: The classification result.
        
    Returns:
        Target model name.
    """
    orchestrator = get_orchestrator()
    return orchestrator.route_only(classification)


def chunk(text: str) -> tuple[List[str], List[ChunkMetadata]]:
    """
    Chunk text into smaller pieces.
    
    Args:
        text: The text to chunk.
        
    Returns:
        Tuple of (list of chunks, list of metadata).
    """
    orchestrator = get_orchestrator()
    return orchestrator.chunk_only(text)


def should_chunk(text: str) -> bool:
    """
    Check if text should be chunked based on length.
    
    Args:
        text: The text to check.
        
    Returns:
        True if chunking is recommended.
    """
    orchestrator = get_orchestrator()
    return orchestrator.chunker.should_chunk(text)


def list_workflows() -> List[str]:
    """
    List all available workflows.
    
    Returns:
        List of workflow names.
    """
    orchestrator = get_orchestrator()
    return orchestrator.get_available_workflows()


def reload_config() -> None:
    """Reload configuration from files."""
    orchestrator = get_orchestrator()
    orchestrator.reload_config()


# Re-export commonly used items
__all__ = [
    # Functions
    "init",
    "process",
    "classify",
    "route",
    "chunk",
    "should_chunk",
    "list_workflows",
    "reload_config",
    "get_orchestrator",
    # Classes
    "WorkflowRegistry",
    # Models
    "ClassificationResult",
    "ComplexityLevel",
    "ProcessingResult",
    "ChunkMetadata",
]
