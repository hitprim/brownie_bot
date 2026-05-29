"""Локальная разработка через polling (вместо webhook).

Запуск: uv run python -m src.dev
"""
import asyncio
import logging

from src.bot.setup import get_bot, get_dispatcher
from src.config import settings
from src.db.session import dispose_engine

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("domovoy.dev")


async def main() -> None:
    bot = get_bot()
    dp = get_dispatcher()

    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Starting polling (dev mode)")
    try:
        await dp.start_polling(bot, allowed_updates=["message"])
    finally:
        await bot.session.close()
        await dispose_engine()


if __name__ == "__main__":
    asyncio.run(main())
