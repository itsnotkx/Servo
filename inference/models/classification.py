"""Classification models using Pydantic for structured output."""

from typing import Any, Optional
from pydantic import BaseModel, Field


class ClassificationResult(BaseModel):
    """Structured classification output from the classifier model."""

    category_id: str = Field(
        description="The selected category identifier"
    )
    category_name: str = Field(
        description="The selected category display name"
    )
    reasoning: str = Field(
        description="Brief explanation for the classification decision"
    )
    requires_chunking: bool = Field(
        default=False,
        description="Whether the input is too long and requires chunking"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Classification confidence score"
    )


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
    selected_category: dict[str, Any] = Field(
        description="Resolved category metadata used for routing"
    )
    llm_response: Optional[str] = Field(
        default=None,
        description="Provider response generated from the routed model"
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
