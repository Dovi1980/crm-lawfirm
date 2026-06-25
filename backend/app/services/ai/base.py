"""
Provider-agnostic interface for chat-style LLM calls.

Every concrete provider (Anthropic, OpenAI, Gemini, future ones) implements
this interface. The rest of the application — services, routers, prompts —
depends only on `BaseAIProvider`. Swapping providers is a config change.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator, Literal


Role = Literal["user", "assistant"]


@dataclass
class AIMessage:
    role: Role
    content: str


class ProviderError(RuntimeError):
    """Raised when the upstream provider fails or is misconfigured."""


class BaseAIProvider(ABC):
    """
    Minimal contract for a chat-completion provider.

    `messages` is a flat list of user/assistant turns. The optional `system`
    parameter carries instructions that should never be mixed into a user
    turn (some providers route it to a dedicated channel, others prepend it).
    """

    #: Human-readable name for logs and error messages.
    name: str = "base"

    @abstractmethod
    async def complete(
        self,
        messages: list[AIMessage],
        *,
        system: str | None = None,
        model: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> str:
        """Return the full assistant response as a string."""

    @abstractmethod
    async def stream(
        self,
        messages: list[AIMessage],
        *,
        system: str | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        """Yield response text chunks as they arrive."""
        # pragma: no cover - abstract; subclasses implement.
        if False:
            yield ""
