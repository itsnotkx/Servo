from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


Role = Literal["system", "user", "assistant"]


@dataclass
class Message:
    role: Role
    content: str


@dataclass
class Conversation:
    """
    Simple conversation buffer.

    The Servo backend currently accepts a single `prompt` string, so this object
    compiles message history into a single prompt.
    """

    system_prompt: str | None = None
    max_turns: int = 10
    messages: list[Message] = field(default_factory=list)

    def add_user(self, content: str) -> None:
        self.messages.append(Message(role="user", content=content))
        self._trim()

    def add_assistant(self, content: str) -> None:
        self.messages.append(Message(role="assistant", content=content))
        self._trim()

    def build_prompt(self, next_user_message: str | None = None) -> str:
        parts: list[str] = []
        if self.system_prompt:
            parts.append(f"System:\n{self.system_prompt}\n")

        for m in self.messages:
            label = "User" if m.role == "user" else "Assistant"
            parts.append(f"{label}:\n{m.content}\n")

        if next_user_message is not None:
            parts.append(f"User:\n{next_user_message}\n")

        return "\n".join(parts).strip()

    def _trim(self) -> None:
        if self.max_turns <= 0:
            return
        max_messages = self.max_turns * 2
        if len(self.messages) > max_messages:
            self.messages = self.messages[-max_messages:]

