"""Main orchestrator for the right-sizing pipeline."""

from typing import Optional, List, Tuple

from .config_loader import ConfigLoader
from ..configs.user_classification_profiles import get_user_profile
from ..services.classifier import PromptClassifier
from ..services.router import LLMRouter
from ..services.chunker import ChunkingService
from ..services.provider_google_ai_studio import GoogleAIStudioProvider
from ..models.classification import ProcessingResult, ClassificationResult, ChunkMetadata


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
        self.google_provider = GoogleAIStudioProvider()
    
    def process(
        self, 
        prompt: str, 
        user_id: str,
        use_quick_classify: bool = False
    ) -> ProcessingResult:
        """
        Process a prompt through the right-sizing pipeline.
        
        Args:
            prompt: The user prompt to process.
            user_id: User identifier for category profile lookup.
            use_quick_classify: Use heuristic classification instead of model.
            
        Returns:
            ProcessingResult with classification, routing, and chunking info.
        """
        profile = get_user_profile(user_id)

        # Step 1: Check if chunking is needed (auto mode assumed)
        chunks: Optional[List[str]] = None
        chunk_metadata: Optional[List[ChunkMetadata]] = None
        
        if self.chunker.should_chunk(prompt):
            chunks, chunk_metadata = self.chunker.chunk(prompt)
        
        # Step 2: Classify the prompt (use first chunk if chunked)
        sample = chunks[0] if chunks else prompt
        
        if use_quick_classify:
            # Use heuristic classification
            classification = self.classifier.quick_classify(sample, profile)
            classification.requires_chunking = chunks is not None
        else:
            # Use model-based classification
            classification = self.classifier.classify(sample, profile)
            # Update chunking flag based on actual chunking if not already set correctly
            if chunks is not None:
                classification.requires_chunking = True
        
        # Step 3: Route to appropriate category/model
        selected_category = self.router.route(classification, profile)
        target_model = selected_category.model_id

        # Step 4: Invoke provider with original prompt
        self.config_loader.validate_required_env(["GOOGLE_AI_STUDIO_API_KEY"])
        llm_response = self.google_provider.generate(prompt, selected_category)
        
        return ProcessingResult(
            classification=classification,
            target_model=target_model,
            selected_category=selected_category.model_dump(),
            llm_response=llm_response,
            chunks=chunks,
            chunk_metadata=chunk_metadata,
            requires_aggregation=chunks is not None and len(chunks) > 1
        )
    
    def classify_only(self, prompt: str, user_id: str, use_quick: bool = False) -> ClassificationResult:
        """
        Classify a prompt without routing.
        
        Args:
            prompt: The prompt to classify.
            user_id: User identifier for category profile lookup.
            use_quick: Use heuristic classification.
            
        Returns:
            ClassificationResult.
        """
        profile = get_user_profile(user_id)
        if use_quick:
            classification = self.classifier.quick_classify(prompt, profile)
            classification.requires_chunking = self.chunker.should_chunk(prompt)
            return classification
        return self.classifier.classify(prompt, profile)
    
    def route_only(self, user_id: str, classification: ClassificationResult) -> str:
        """
        Route a classification to a model.
        
        Args:
            user_id: User identifier for category profile lookup.
            classification: The classification result.
            
        Returns:
            Target model name.
        """
        profile = get_user_profile(user_id)
        selected_category = self.router.route(classification, profile)
        return selected_category.model_id
    
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
        self.google_provider = GoogleAIStudioProvider()
