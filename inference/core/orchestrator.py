"""Main orchestrator for the right-sizing pipeline."""

from typing import Optional, Dict, List, Tuple

from .config_loader import ConfigLoader
from ..services.classifier import PromptClassifier
from ..services.router import LLMRouter
from ..services.chunker import ChunkingService
from ..models.classification import ProcessingResult, ClassificationResult, ChunkMetadata, ComplexityLevel


class WorkflowOrchestrator:
    """
    Orchestrates the right-sizing workflow.
    
    Coordinates classification, chunking, and routing to process prompts.
    """
    
    def __init__(
        self, 
        config_path: Optional[str] = None,
        env_path: Optional[str] = None
    ):
        """
        Initialize the orchestrator.
        
        Args:
            config_path: Path to config.yaml.
            env_path: Path to .env.local.
        """
        # Load configuration
        self.config_loader = ConfigLoader(config_path, env_path)
        self.config = self.config_loader.load()
        
        # Initialize services
        self.classifier = PromptClassifier(self.config.get("classifier", {}))
        self.router = LLMRouter(self.config.get("routing", {}))
        self.chunker = ChunkingService(self.config.get("chunking", {}))
    
    def process(
        self, 
        prompt: str, 
        use_quick_classify: bool = False
    ) -> ProcessingResult:
        """
        Process a prompt through the right-sizing pipeline.
        
        Args:
            prompt: The user prompt to process.
            use_quick_classify: Use heuristic classification instead of model.
            
        Returns:
            ProcessingResult with classification, routing, and chunking info.
        """
        # Step 1: Check if chunking is needed (auto mode assumed)
        chunks: Optional[List[str]] = None
        chunk_metadata: Optional[List[ChunkMetadata]] = None
        
        if self.chunker.should_chunk(prompt):
            chunks, chunk_metadata = self.chunker.chunk(prompt)
        
        # Step 2: Classify the prompt (use first chunk if chunked)
        sample = chunks[0] if chunks else prompt
        
        if use_quick_classify:
            # Use heuristic classification
            complexity = self.classifier.quick_classify(sample)
            classification = ClassificationResult(
                complexity=complexity,
                reasoning="Quick heuristic classification",
                requires_chunking=chunks is not None,
                suggested_model_tier=complexity.value,
                confidence=0.7
            )
        else:
            # Use model-based classification
            classification = self.classifier.classify(sample)
            # Update chunking flag based on actual chunking if not already set correctly
            if chunks is not None:
                classification.requires_chunking = True
        
        # Step 3: Route to appropriate model
        target_model = self.router.route(classification)
        
        return ProcessingResult(
            classification=classification,
            target_model=target_model,
            chunks=chunks,
            chunk_metadata=chunk_metadata,
            requires_aggregation=chunks is not None and len(chunks) > 1
        )
    
    def classify_only(self, prompt: str, use_quick: bool = False) -> ClassificationResult:
        """
        Classify a prompt without routing.
        
        Args:
            prompt: The prompt to classify.
            use_quick: Use heuristic classification.
            
        Returns:
            ClassificationResult.
        """
        if use_quick:
            complexity = self.classifier.quick_classify(prompt)
            return ClassificationResult(
                complexity=complexity,
                reasoning="Quick heuristic classification",
                requires_chunking=self.chunker.should_chunk(prompt),
                suggested_model_tier=complexity.value,
                confidence=0.7
            )
        return self.classifier.classify(prompt)
    
    def route_only(self, classification: ClassificationResult) -> str:
        """
        Route a classification to a model.
        
        Args:
            classification: The classification result.
            
        Returns:
            Target model name.
        """
        return self.router.route(classification)
    
    def chunk_only(self, text: str) -> Tuple[List[str], List[ChunkMetadata]]:
        """
        Chunk text without classification.
        
        Args:
            text: The text to chunk.
            
        Returns:
            Tuple of (chunks, metadata).
        """
        return self.chunker.chunk(text)
    
    def reload_config(self) -> None:
        """Reload configuration from files."""
        self.config = self.config_loader.load()
        
        # Reinitialize services with new config
        self.classifier = PromptClassifier(self.config.get("classifier", {}))
        self.router = LLMRouter(self.config.get("routing", {}))
        self.chunker = ChunkingService(self.config.get("chunking", {}))
