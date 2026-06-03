import asyncio
import logging
from functools import lru_cache

from src.config import settings

logger = logging.getLogger("domovoy.memory")


class UserMemory:
    """Обёртка над облачным mem0. Изолирует SDK от остального кода.

    Все вызовы внешнего сервиса не должны ронять бота: ошибки логируются,
    поиск возвращает [], сохранение/очистка молча пропускаются.
    SDK синхронный — выполняем в отдельном потоке, чтобы не блокировать event loop.
    """

    def __init__(self, api_key: str):
        from mem0 import MemoryClient

        self._client = MemoryClient(api_key=api_key)

    async def search(self, user_id: str, query: str, limit: int = 5) -> list[str]:
        """Релевантные факты о пользователе под текущий запрос."""
        try:
            response = await asyncio.to_thread(
                self._client.search,
                query,
                filters={"user_id": user_id},
                top_k=limit,
            )
            results = response.get("results", []) if isinstance(response, dict) else response
            return [m["memory"] for m in results if m.get("memory")]
        except Exception:
            logger.warning("mem0 search failed for user=%s", user_id, exc_info=True)
            return []

    async def add(self, user_id: str, messages: list[dict[str, str]]) -> None:
        """Сохранить факты из диалога. mem0 сам извлекает факты из сообщений."""
        try:
            await asyncio.to_thread(self._client.add, messages, user_id=user_id)
        except Exception:
            logger.warning("mem0 add failed for user=%s", user_id, exc_info=True)

    async def forget(self, user_id: str) -> None:
        """Полностью очистить память пользователя."""
        try:
            await asyncio.to_thread(self._client.delete_all, user_id=user_id)
        except Exception:
            logger.warning("mem0 delete_all failed for user=%s", user_id, exc_info=True)


@lru_cache
def get_memory() -> UserMemory | None:
    """Клиент памяти или None, если ключ не задан (память выключена)."""
    if not settings.mem0_api_key:
        return None
    try:
        return UserMemory(settings.mem0_api_key)
    except Exception:
        logger.warning("Could not init mem0 client; memory disabled", exc_info=True)
        return None


def memory_block(facts: list[str]) -> str:
    """Готовый блок для подмешивания в системный промпт. Пусто, если фактов нет."""
    if not facts:
        return ""
    joined = "; ".join(f.strip() for f in facts if f.strip())
    if not joined:
        return ""
    return (
        f"Что известно о пользователе из прошлых диалогов: {joined}. "
        "Учитывай это и не переспрашивай уже известное."
    )
