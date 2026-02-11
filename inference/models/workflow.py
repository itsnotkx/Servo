"""Workflow configuration models."""

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional


class WorkflowStep(BaseModel):
    """Configuration for a single workflow step."""

    name: str = Field(description="Name of the workflow step")
    enabled: bool = Field(default=True, description="Whether this step is enabled")
    config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Step-specific configuration"
    )


class WorkflowConfig(BaseModel):
    """Complete workflow configuration."""

    name: str = Field(description="Name of the workflow")
    steps: List[WorkflowStep] = Field(
        default_factory=list,
        description="Ordered list of workflow steps"
    )
    fallback_tier: str = Field(
        default="thinking",
        description="Default tier to use if classification fails"
    )

    # Feature flags
    preprocessor: bool = Field(
        default=True,
        description="Enable text preprocessing"
    )
    classifier: bool = Field(
        default=True,
        description="Enable prompt classification"
    )
    chunker: str = Field(
        default="auto",
        description="Chunking mode: 'auto', 'always', 'never'"
    )
    router: bool = Field(
        default=True,
        description="Enable model routing"
    )


class TierConfig(BaseModel):
    """Configuration for a model tier."""

    description: str = Field(description="Human-readable tier description")
    model: Optional[str] = Field(
        default=None,
        description="Model name (loaded from environment)"
    )


class RoutingConfig(BaseModel):
    """Routing configuration with tier definitions."""

    tiers: Dict[str, TierConfig] = Field(
        default_factory=dict,
        description="Tier name to configuration mapping"
    )


class ChunkingConfig(BaseModel):
    """Chunking configuration."""

    strategy: str = Field(
        default="semantic",
        description="Chunking strategy: 'semantic' or 'recursive'"
    )
    max_chunk_size: int = Field(
        default=4096,
        description="Maximum tokens per chunk"
    )
    overlap: int = Field(
        default=200,
        description="Token overlap between chunks"
    )
    threshold_tokens: int = Field(
        default=8000,
        description="Token threshold to trigger chunking"
    )


class AppConfig(BaseModel):
    """Top-level application configuration."""

    routing: RoutingConfig = Field(default_factory=RoutingConfig)
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    workflows: Dict[str, WorkflowConfig] = Field(default_factory=dict)
