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

