"""
Provider-agnostic interface for chat-style LLM calls.

Every concrete provider (Anthropic, OpenAI, Gemini, future ones) implements
this interface. The rest of the application — services, routers, prompts —
depends only on `BaseAIProvider`. Swapping providers is a config change.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator, Literal


Role = Literal["user", "assistant"]


@dataclass
class AIAttachment:
    """A binary file (PDF / image) sent alongside a user message for multimodal input."""
    mime_type: str
    data: bytes  # raw bytes; each provider encodes as needed (base64, etc.)
    filename: str = ""


@dataclass
class AIMessage:
    role: Role
    content: str
    attachments: list["AIAttachment"] = field(default_factory=list)


class ProviderError(RuntimeError):
    """Raised when the upstream provider fails or is misconfigured."""


def reject_attachments_if_present(messages: list["AIMessage"], provider_name: str) -> None:
    """Guard for providers that don't yet implement multimodal input."""
    if any(m.attachments for m in messages):
        raise ProviderError(
            f"El proveedor '{provider_name}' todavía no soporta lectura de archivos adjuntos. "
            "Usá Gemini para esta función o implementá multimodal en su adaptador."
        )


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
