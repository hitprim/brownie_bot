import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

logger = logging.getLogger("domovoy.bot")


class LoggingMiddleware(BaseMiddleware):
    """Логирует только метаданные, НЕ содержимое сообщений."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        message = getattr(event, "message", None) or getattr(event, "edited_message", None)
        if isinstance(message, Message):
            kind = "voice" if message.voice else "text"
            user_id = message.from_user.id if message.from_user else "?"
            logger.info("Incoming update: user=%s kind=%s", user_id, kind)
        return await handler(event, data)
