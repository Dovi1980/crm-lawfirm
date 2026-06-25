"""
Factory that returns the configured AIProvider instance.

The choice is driven by `settings.AI_PROVIDER` (anthropic | openai | gemini).
Providers are instantiated lazily and cached for the process lifetime.
"""
from __future__ import annotations

from functools import lru_cache

from app.config import settings
from app.services.ai.base import BaseAIProvider, ProviderError


@lru_cache(maxsize=1)
def get_ai_provider() -> BaseAIProvider:
    provider_name = settings.AI_PROVIDER.lower().strip()

    if provider_name == "anthropic":
        from app.services.ai.anthropic_provider import AnthropicProvider
        return AnthropicProvider(
            api_key=settings.ANTHROPIC_API_KEY,
            default_model=settings.AI_MODEL_DEFAULT,
        )

    if provider_name == "openai":
        from app.services.ai.openai_provider import OpenAIProvider
        return OpenAIProvider(
            api_key=settings.OPENAI_API_KEY,
            default_model=settings.AI_MODEL_DEFAULT,
            base_url=settings.OPENAI_BASE_URL or None,
        )

    if provider_name == "gemini":
        from app.services.ai.gemini_provider import GeminiProvider
        return GeminiProvider(
            api_key=settings.GEMINI_API_KEY,
            default_model=settings.AI_MODEL_DEFAULT,
        )

    raise ProviderError(
        f"AI_PROVIDER desconocido: {settings.AI_PROVIDER!r}. "
        "Valores válidos: anthropic, openai, gemini."
    )
