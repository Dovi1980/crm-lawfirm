"""OpenAI / Azure OpenAI adapter for the BaseAIProvider interface."""
from __future__ import annotations

from typing import AsyncIterator

from app.services.ai.base import AIMessage, BaseAIProvider, ProviderError


class OpenAIProvider(BaseAIProvider):
    name = "openai"

    def __init__(self, api_key: str, default_model: str, base_url: str | None = None):
        if not api_key:
            raise ProviderError("OPENAI_API_KEY no configurada")
        try:
            from openai import AsyncOpenAI
        except ImportError as e:
            raise ProviderError(
                "Paquete 'openai' no instalado. Instalar con: pip install openai"
            ) from e

        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self._client = AsyncOpenAI(**kwargs)
        self._default_model = default_model

    def _build_messages(self, messages: list[AIMessage], system: str | None) -> list[dict]:
        out: list[dict] = []
        if system:
            out.append({"role": "system", "content": system})
        for m in messages:
            out.append({"role": m.role, "content": m.content})
        return out

    async def complete(
        self,
        messages: list[AIMessage],
        *,
        system: str | None = None,
        model: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> str:
        try:
            response = await self._client.chat.completions.create(
                model=model or self._default_model,
                messages=self._build_messages(messages, system),
                max_tokens=max_tokens,
                temperature=temperature,
            )
        except Exception as e:
            raise ProviderError(f"OpenAI API error: {e}") from e

        return response.choices[0].message.content or ""

    async def stream(
        self,
        messages: list[AIMessage],
        *,
        system: str | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        try:
            stream = await self._client.chat.completions.create(
                model=model or self._default_model,
                messages=self._build_messages(messages, system),
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True,
            )
            async for event in stream:
                delta = event.choices[0].delta.content if event.choices else None
                if delta:
                    yield delta
        except Exception as e:
            raise ProviderError(f"OpenAI streaming error: {e}") from e
