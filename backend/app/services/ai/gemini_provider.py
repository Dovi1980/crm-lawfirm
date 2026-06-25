"""
Google Gemini adapter via raw HTTPS (no extra SDK dependency).

Uses the v1beta `generateContent` / `streamGenerateContent` endpoints with
Server-Sent Events for streaming.
"""
from __future__ import annotations

import json
from typing import AsyncIterator

import httpx

from app.services.ai.base import AIMessage, BaseAIProvider, ProviderError


_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"


class GeminiProvider(BaseAIProvider):
    name = "gemini"

    def __init__(self, api_key: str, default_model: str):
        if not api_key:
            raise ProviderError("GEMINI_API_KEY no configurada")
        self._api_key = api_key
        self._default_model = default_model
        self._client = httpx.AsyncClient(timeout=60.0)

    def _build_body(
        self,
        messages: list[AIMessage],
        system: str | None,
        max_tokens: int,
        temperature: float,
    ) -> dict:
        contents = []
        for m in messages:
            # Gemini calls the assistant role "model".
            role = "model" if m.role == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": m.content}]})

        body: dict = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        if system:
            body["systemInstruction"] = {"parts": [{"text": system}]}
        return body

    async def complete(
        self,
        messages: list[AIMessage],
        *,
        system: str | None = None,
        model: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> str:
        url = f"{_BASE_URL}/models/{model or self._default_model}:generateContent"
        try:
            resp = await self._client.post(
                url,
                params={"key": self._api_key},
                json=self._build_body(messages, system, max_tokens, temperature),
            )
            resp.raise_for_status()
        except httpx.HTTPError as e:
            raise ProviderError(f"Gemini API error: {e}") from e

        data = resp.json()
        try:
            return "".join(
                part["text"]
                for part in data["candidates"][0]["content"]["parts"]
                if "text" in part
            )
        except (KeyError, IndexError) as e:
            raise ProviderError(f"Gemini response shape unexpected: {data}") from e

    async def stream(
        self,
        messages: list[AIMessage],
        *,
        system: str | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        url = f"{_BASE_URL}/models/{model or self._default_model}:streamGenerateContent"
        try:
            async with self._client.stream(
                "POST",
                url,
                params={"key": self._api_key, "alt": "sse"},
                json=self._build_body(messages, system, max_tokens, temperature),
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    payload = line[len("data: "):].strip()
                    if not payload:
                        continue
                    try:
                        chunk = json.loads(payload)
                        for part in chunk["candidates"][0]["content"]["parts"]:
                            if "text" in part:
                                yield part["text"]
                    except (KeyError, IndexError, json.JSONDecodeError):
                        # Final marker / partial frames — skip.
                        continue
        except httpx.HTTPError as e:
            raise ProviderError(f"Gemini streaming error: {e}") from e
