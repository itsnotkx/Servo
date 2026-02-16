from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


def _require(d: dict[str, Any], key: str) -> Any:
    if key not in d:
        raise ValueError(f"Missing key: {key}")
    return d[key]


@dataclass(frozen=True)
class ClassificationResult:
    category_id: str
    category_name: str
    reasoning: str
    requires_chunking: bool
    confidence: float

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "ClassificationResult":
        return ClassificationResult(
            category_id=str(_require(d, "category_id")),
            category_name=str(_require(d, "category_name")),
            reasoning=str(_require(d, "reasoning")),
            requires_chunking=bool(d.get("requires_chunking", False)),
            confidence=float(_require(d, "confidence")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "category_id": self.category_id,
            "category_name": self.category_name,
            "reasoning": self.reasoning,
            "requires_chunking": self.requires_chunking,
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class ClassificationCategory:
    id: str
    name: str
    description: str
    provider: str
    endpoint: str
    model_id: str
    request_defaults: Optional[dict[str, Any]] = None

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "ClassificationCategory":
        return ClassificationCategory(
            id=str(_require(d, "id")),
            name=str(_require(d, "name")),
            description=str(_require(d, "description")),
            provider=str(_require(d, "provider")),
            endpoint=str(_require(d, "endpoint")),
            model_id=str(_require(d, "model_id")),
            request_defaults=d.get("request_defaults"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "provider": self.provider,
            "endpoint": self.endpoint,
            "model_id": self.model_id,
            "request_defaults": self.request_defaults,
        }


@dataclass(frozen=True)
class ChunkMetadata:
    chunk_index: int
    total_chunks: int
    start_char: int
    end_char: int
    token_estimate: Optional[int] = None

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "ChunkMetadata":
        return ChunkMetadata(
            chunk_index=int(_require(d, "chunk_index")),
            total_chunks=int(_require(d, "total_chunks")),
            start_char=int(_require(d, "start_char")),
            end_char=int(_require(d, "end_char")),
            token_estimate=None if d.get("token_estimate") is None else int(d["token_estimate"]),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunk_index": self.chunk_index,
            "total_chunks": self.total_chunks,
            "start_char": self.start_char,
            "end_char": self.end_char,
            "token_estimate": self.token_estimate,
        }


@dataclass(frozen=True)
class ProcessingResult:
    classification: ClassificationResult
    target_model: str
    selected_category: ClassificationCategory
    llm_response: Optional[str] = None
    chunks: Optional[list[str]] = None
    chunk_metadata: Optional[list[ChunkMetadata]] = None
    requires_aggregation: bool = False

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "ProcessingResult":
        classification = ClassificationResult.from_dict(_require(d, "classification"))
        selected_category = ClassificationCategory.from_dict(_require(d, "selected_category"))
        chunks = d.get("chunks")
        chunk_metadata_raw = d.get("chunk_metadata")
        return ProcessingResult(
            classification=classification,
            target_model=str(_require(d, "target_model")),
            selected_category=selected_category,
            llm_response=d.get("llm_response"),
            chunks=None if chunks is None else [str(x) for x in chunks],
            chunk_metadata=None
            if chunk_metadata_raw is None
            else [ChunkMetadata.from_dict(x) for x in chunk_metadata_raw],
            requires_aggregation=bool(d.get("requires_aggregation", False)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "classification": self.classification.to_dict(),
            "target_model": self.target_model,
            "selected_category": self.selected_category.to_dict(),
            "llm_response": self.llm_response,
            "chunks": self.chunks,
            "chunk_metadata": None
            if self.chunk_metadata is None
            else [m.to_dict() for m in self.chunk_metadata],
            "requires_aggregation": self.requires_aggregation,
        }


@dataclass(frozen=True)
class TiersResponse:
    tiers: dict[str, str]

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "TiersResponse":
        tiers = _require(d, "tiers")
        if not isinstance(tiers, dict):
            raise ValueError("tiers must be a dict")
        return TiersResponse(tiers={str(k): str(v) for k, v in tiers.items()})

    def to_dict(self) -> dict[str, Any]:
        return {"tiers": dict(self.tiers)}


@dataclass(frozen=True)
class RouteResponse:
    target_model: str

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "RouteResponse":
        return RouteResponse(target_model=str(_require(d, "target_model")))

    def to_dict(self) -> dict[str, Any]:
        return {"target_model": self.target_model}


@dataclass(frozen=True)
class CategoriesResponse:
    user_id: str
    default_category_id: str
    categories: list[ClassificationCategory]

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "CategoriesResponse":
        categories_raw = _require(d, "categories")
        return CategoriesResponse(
            user_id=str(_require(d, "user_id")),
            default_category_id=str(_require(d, "default_category_id")),
            categories=[ClassificationCategory.from_dict(c) for c in categories_raw],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "default_category_id": self.default_category_id,
            "categories": [c.to_dict() for c in self.categories],
        }

