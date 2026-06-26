"""
Google Gemini adapter via raw HTTPS (no extra SDK dependency).

Uses the v1beta `generateContent` / `streamGenerateContent` endpoints with
Server-Sent Events for streaming.
"""
from __future__ import annotations

import asyncio
import base64
import json
from typing import AsyncIterator

import httpx

from app.services.ai.base import AIMessage, BaseAIProvider, ProviderError

# Google devuelve 503 (sobrecarga) y 429 (rate limit) de forma transitoria.
# Reintentamos con backoff corto antes de propagar el error al usuario.
_RETRYABLE_STATUS = {429, 500, 503}
_MAX_RETRIES = 3


_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"


def _thinking_budget(model: str) -> int:
    """
    Tokens de razonamiento interno permitidos por modelo.

    - flash / flash-lite: 0 (deshabilitado). Para resúmenes, chat y redacción
      desde contexto estructurado no aporta y agrega latencia/costo. Estos
      modelos sí admiten thinkingBudget=0.
    - pro y otros: 2048. Pro no permite deshabilitar el thinking (mínimo > 0),
      así que le damos un presupuesto acotado.
    """
    m = model.lower()
    if "flash" in m or "lite" in m:
        return 0
    return 2048


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
        model: str,
    ) -> dict:
        contents = []
        for m in messages:
            # Gemini calls the assistant role "model".
            role = "model" if m.role == "assistant" else "user"
            parts: list[dict] = []
            if m.content:
                parts.append({"text": m.content})
            for att in m.attachments:
                parts.append({
                    "inline_data": {
                        "mime_type": att.mime_type,
                        "data": base64.standard_b64encode(att.data).decode("ascii"),
                    }
                })
            contents.append({"role": role, "parts": parts})

        # Gemini 2.5+ models "think" by default, and those thinking tokens are
        # drawn from maxOutputTokens — so a small cap truncates the visible answer
        # mid-sentence. We (a) give the answer its full budget ON TOP of any
        # thinking budget, and (b) disable thinking on flash/lite models where our
        # tasks (summary, chat, drafting from structured context) don't need it.
        thinking_budget = _thinking_budget(model)
        gen_config = {
            "temperature": temperature,
            "maxOutputTokens": max_tokens + thinking_budget,
            "thinkingConfig": {"thinkingBudget": thinking_budget},
        }

        body: dict = {"contents": contents, "generationConfig": gen_config}
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
        model_used = model or self._default_model
        url = f"{_BASE_URL}/models/{model_used}:generateContent"
        body = self._build_body(messages, system, max_tokens, temperature, model_used)

        last_exc: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                resp = await self._client.post(url, params={"key": self._api_key}, json=body)
                resp.raise_for_status()
                break
            except httpx.HTTPStatusError as e:
                last_exc = e
                if e.response.status_code in _RETRYABLE_STATUS and attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(1.5 * (attempt + 1))
                    continue
                raise ProviderError(f"Gemini API error: {e}") from e
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
        model_used = model or self._default_model
        url = f"{_BASE_URL}/models/{model_used}:streamGenerateContent"
        body = self._build_body(messages, system, max_tokens, temperature, model_used)

        for attempt in range(_MAX_RETRIES):
            started = False  # ¿ya emitimos algún chunk? si sí, no reintentamos
            try:
                async with self._client.stream(
                    "POST",
                    url,
                    params={"key": self._api_key, "alt": "sse"},
                    json=body,
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
                                    started = True
                                    yield part["text"]
                        except (KeyError, IndexError, json.JSONDecodeError):
                            # Final marker / partial frames — skip.
                            continue
                return  # stream completo
            except httpx.HTTPStatusError as e:
                retryable = e.response.status_code in _RETRYABLE_STATUS
                if retryable and not started and attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(1.5 * (attempt + 1))
                    continue
                raise ProviderError(f"Gemini streaming error: {e}") from e
            except httpx.HTTPError as e:
                raise ProviderError(f"Gemini streaming error: {e}") from e
