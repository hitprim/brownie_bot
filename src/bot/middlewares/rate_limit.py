from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, time
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import User
from src.db.repositories.conversation_repo import ConversationRepository
from src.services.config_service import DEFAULTS


class RateLimitMiddleware(BaseMiddleware):
    """Дневной лимит запросов на пользователя. Считает сообщения за сегодня по БД.

    Работает на сессии и юзере, которые кладёт UserMiddleware (регистрируется раньше).
    """

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

        session: AsyncSession | None = data.get("session")
        user: User | None = data.get("user")
        if session is None or user is None:
            return await handler(event, data)

        limit = DEFAULTS["free_requests_per_day"]
        start_of_day = datetime.combine(datetime.now(UTC).date(), time.min, tzinfo=UTC)
        count = await ConversationRepository(session).count_user_messages_since(
            user.id, start_of_day
        )

        if count >= limit:
            await event.answer(
                "На сегодня лимит бесплатных запросов исчерпан. "
                "Возвращайтесь завтра 🙂"
            )
            return None

        return await handler(event, data)
