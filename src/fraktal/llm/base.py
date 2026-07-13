"""Abstract LLM provider interface — all providers implement this."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Message:
    role: str  # system | user | assistant | tool
    content: str | None = None
    tool_call_id: str | None = None
    tool_calls: list["ToolCall"] | None = None


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema for the function


@dataclass
class LLMResponse:
    content: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)
    finish_reason: str = "stop"
    usage: dict[str, int] | None = None


class LLMProvider(ABC):
    """Abstract base for an LLM provider.

    Implementations: DeepSeekProvider, OpenAIProvider, AnthropicProvider.
    """

    @abstractmethod
    def chat(
        self,
        messages: list[Message],
        *,
        system: str | None = None,
        tools: list[ToolSpec] | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> LLMResponse:
        """Send a chat completion and return a normalized response."""
        ...

    @abstractmethod
    def check_connection(self) -> dict[str, Any]:
        """Verify API connectivity. Returns {"ok": True/False, ...}."""
        ...
