"""Anthropic Claude adapter for the BaseAIProvider interface."""
from __future__ import annotations

from typing import AsyncIterator

from app.services.ai.base import (
    AIMessage,
    BaseAIProvider,
    ProviderError,
    reject_attachments_if_present,
)


class AnthropicProvider(BaseAIProvider):
    name = "anthropic"

    def __init__(self, api_key: str, default_model: str):
        if not api_key:
            raise ProviderError("ANTHROPIC_API_KEY no configurada")
        try:
            from anthropic import AsyncAnthropic
        except ImportError as e:
            raise ProviderError(
                "Paquete 'anthropic' no instalado. Instalar con: pip install anthropic"
            ) from e

        self._client = AsyncAnthropic(api_key=api_key)
        self._default_model = default_model

    async def complete(
        self,
        messages: list[AIMessage],
        *,
        system: str | None = None,
        model: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> str:
        reject_attachments_if_present(messages, self.name)
        kwargs = {
            "model": model or self._default_model,
            "max_tokens": max_tokens,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }
        if system:
            kwargs["system"] = system
        # temperature is rejected on some 4.7+ models; pass only when supported.
        if not _is_no_sampling_model(kwargs["model"]):
            kwargs["temperature"] = temperature

        try:
            response = await self._client.messages.create(**kwargs)
        except Exception as e:
            raise ProviderError(f"Anthropic API error: {e}") from e

        return "".join(block.text for block in response.content if block.type == "text")

    async def stream(
        self,
        messages: list[AIMessage],
        *,
        system: str | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        reject_attachments_if_present(messages, self.name)
        kwargs = {
            "model": model or self._default_model,
            "max_tokens": max_tokens,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }
        if system:
            kwargs["system"] = system
        if not _is_no_sampling_model(kwargs["model"]):
            kwargs["temperature"] = temperature

        try:
            async with self._client.messages.stream(**kwargs) as stream:
                async for text in stream.text_stream:
                    yield text
        except Exception as e:
            raise ProviderError(f"Anthropic streaming error: {e}") from e


def _is_no_sampling_model(model: str) -> bool:
    """Models that reject temperature/top_p (Claude Opus 4.7+ and Fable 5)."""
    no_sample_prefixes = ("claude-opus-4-7", "claude-opus-4-8", "claude-fable-5")
    return model.startswith(no_sample_prefixes)
