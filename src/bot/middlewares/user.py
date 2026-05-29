from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from src.db.session import async_session_factory
from src.services.user_service import UserService


class UserMiddleware(BaseMiddleware):
    """Создаёт/обновляет юзера в БД и кладёт session + user в data хендлера."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message) or event.from_user is None:
            return await handler(event, data)

        tg = event.from_user
        async with async_session_factory() as session:
            service = UserService(session)
            user = await service.get_or_create(
                telegram_id=tg.id,
                username=tg.username,
                first_name=tg.first_name,
                language_code=tg.language_code or "ru",
            )
            data["session"] = session
            data["user"] = user
            data["user_dto"] = UserService.to_dto(user)
            return await handler(event, data)
