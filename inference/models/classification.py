"""Classification models using Pydantic for structured output."""

from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional


class ComplexityLevel(str, Enum):
    """Complexity levels for prompt classification."""

    SIMPLE = "simple"      # Fact retrieval, simple QA, lightweight requests
    THINKING = "thinking"  # General reasoning and synthesis tasks
    COMPLEX = "complex"    # Multi-step reasoning, deep analysis, advanced tasks


class ClassificationResult(BaseModel):
    """Structured classification output from the classifier model."""

    complexity: ComplexityLevel = Field(
        description="The complexity level of the prompt"
    )
    reasoning: str = Field(
        description="Brief explanation for the classification decision"
    )
    requires_chunking: bool = Field(
        default=False,
        description="Whether the input is too long and requires chunking"
    )
    suggested_model_tier: str = Field(
        description="Recommended model tier based on classification"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Classification confidence score"
    )

    class Config:
        use_enum_values = True


class ChunkMetadata(BaseModel):
    """Metadata for a processed chunk."""

    chunk_index: int = Field(description="Index of this chunk in the sequence")
    total_chunks: int = Field(description="Total number of chunks")
    start_char: int = Field(description="Starting character position in original text")
    end_char: int = Field(description="Ending character position in original text")
    token_estimate: Optional[int] = Field(
        default=None,
        description="Estimated token count for this chunk"
    )


class ProcessingResult(BaseModel):
    """Complete result from the right-sizing workflow."""

    classification: ClassificationResult = Field(
        description="Classification result for the prompt"
    )
    target_model: str = Field(
        description="Selected model for processing"
    )
    chunks: Optional[list[str]] = Field(
        default=None,
        description="List of chunks if chunking was applied"
    )
    chunk_metadata: Optional[list[ChunkMetadata]] = Field(
        default=None,
        description="Metadata for each chunk"
    )
    requires_aggregation: bool = Field(
        default=False,
        description="Whether responses need to be aggregated from multiple chunks"
    )
