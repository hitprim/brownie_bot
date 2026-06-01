from functools import lru_cache

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from src.config import settings


@lru_cache
def get_bot() -> Bot:
    return Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode="HTML"),
    )


@lru_cache
def get_dispatcher() -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())
    _register(dp)
    return dp


def _register(dp: Dispatcher) -> None:
    from src.bot.handlers import callbacks, start, text, voice
    from src.bot.middlewares.logging import LoggingMiddleware
    from src.bot.middlewares.rate_limit import RateLimitMiddleware
    from src.bot.middlewares.user import UserMiddleware

    dp.update.middleware(LoggingMiddleware())
    dp.message.middleware(UserMiddleware())
    dp.message.middleware(RateLimitMiddleware())
    dp.callback_query.middleware(UserMiddleware())

    dp.include_router(start.router)
    dp.include_router(voice.router)
    dp.include_router(callbacks.router)
    dp.include_router(text.router)
