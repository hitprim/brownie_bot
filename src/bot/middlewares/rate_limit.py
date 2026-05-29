from collections.abc import Awaitable, Callable
from datetime import date
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from src.services.config_service import DEFAULTS


class RateLimitMiddleware(BaseMiddleware):
    """Простой дневной лимит запросов на пользователя (in-memory).

    v0.1: счётчик в памяти процесса. При горизонтальном масштабировании
    нужно вынести в БД/Redis.
    """

    def __init__(self) -> None:
        self._counters: dict[int, tuple[date, int]] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message) or event.from_user is None:
            return await handler(event, data)

        # команды не лимитируем
        if event.text and event.text.startswith("/"):
            return await handler(event, data)

        limit = DEFAULTS["free_requests_per_day"]
        today = date.today()
        user_id = event.from_user.id
        stored_date, count = self._counters.get(user_id, (today, 0))
        if stored_date != today:
            count = 0

        if count >= limit:
            await event.answer(
                "На сегодня лимит бесплатных запросов исчерпан. "
                "Возвращайтесь завтра 🙂"
            )
            return None

        self._counters[user_id] = (today, count + 1)
        return await handler(event, data)
