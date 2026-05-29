import asyncio
import json
import logging
from functools import lru_cache
from typing import Any

import httpx

from src.config import settings
from src.llm.base import LLMMessage

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


class LLMError(Exception):
    pass


class OpenRouterProvider:
    """DeepSeek через OpenRouter с fallback на Claude Haiku."""

    def __init__(
        self,
        api_key: str,
        model: str,
        fallback_model: str | None = None,
        timeout: float = 60.0,
    ):
        self.api_key = api_key
        self.model = model
        self.fallback_model = fallback_model
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": settings.base_url,
            "X-Title": "Domovoy",
        }

    async def _request(
        self,
        model: str,
        messages: list[LLMMessage],
        temperature: float,
        max_tokens: int | None,
        json_mode: bool,
    ) -> str:
        payload: dict[str, Any] = {
            "model": model,
            "messages": [m.model_dump() for m in messages],
            "temperature": temperature,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                OPENROUTER_URL, headers=self._headers(), json=payload
            )
            response.raise_for_status()
            data = response.json()
        return data["choices"][0]["message"]["content"]

    async def _complete_with_fallback(
        self,
        messages: list[LLMMessage],
        temperature: float,
        max_tokens: int | None,
        json_mode: bool,
        retries: int = 2,
    ) -> str:
        models = [self.model]
        if self.fallback_model:
            models.append(self.fallback_model)

        last_error: Exception | None = None
        for model in models:
            for attempt in range(retries):
                try:
                    return await self._request(
                        model, messages, temperature, max_tokens, json_mode
                    )
                except (httpx.HTTPError, KeyError) as exc:
                    last_error = exc
                    backoff = 2**attempt
                    logger.warning(
                        "LLM call failed (model=%s, attempt=%d): %s — retry in %ds",
                        model,
                        attempt + 1,
                        exc,
                        backoff,
                    )
                    await asyncio.sleep(backoff)
        raise LLMError(f"All LLM attempts failed: {last_error}") from last_error

    async def complete(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.4,
        max_tokens: int | None = None,
    ) -> str:
        return await self._complete_with_fallback(
            messages, temperature, max_tokens, json_mode=False
        )

    async def complete_json(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        raw = await self._complete_with_fallback(
            messages, temperature, max_tokens, json_mode=True
        )
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            cleaned = _extract_json(raw)
            if cleaned is not None:
                return cleaned
            raise LLMError(f"LLM returned invalid JSON: {raw[:200]}") from exc


def _extract_json(raw: str) -> dict[str, Any] | None:
    """Достаёт JSON-объект если модель обернула его в markdown или текст."""
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end < start:
        return None
    try:
        return json.loads(raw[start : end + 1])
    except json.JSONDecodeError:
        return None


@lru_cache
def get_llm() -> OpenRouterProvider:
    return OpenRouterProvider(
        api_key=settings.openrouter_api_key,
        model=settings.llm_model,
        fallback_model=settings.llm_fallback_model,
    )
