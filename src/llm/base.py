from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel


class LLMMessage(BaseModel):
    role: str  # "system" | "user" | "assistant"
    content: str


@runtime_checkable
class LLMProvider(Protocol):
    """Единый интерфейс LLM. Смена провайдера — через .env, без изменения кода."""

    async def complete(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.4,
        max_tokens: int | None = None,
    ) -> str:
        """Свободный текстовый ответ."""
        ...

    async def complete_json(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Структурированный ответ (JSON object)."""
        ...
