from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ServoSDKError(Exception):
    message: str

    def __str__(self) -> str:
        return self.message


@dataclass(frozen=True)
class ServoAPIError(ServoSDKError):
    status_code: int
    body: Any | None = None


@dataclass(frozen=True)
class ServoConnectionError(ServoSDKError):
    cause: Exception | None = None


@dataclass(frozen=True)
class ServoAuthenticationError(ServoSDKError):
    status_code: int = 401


@dataclass(frozen=True)
class ServoDecompositionError(ServoSDKError):
    raw_content: str | None = None


class ServoEmbeddingError(ServoSDKError):
    """Raised when subtask embedding or ContextDB operations fail."""
    def __init__(self, message: str, cause: Exception | None = None):
        super().__init__(f"Embedding error: {message}")
        self.__cause__ = cause

