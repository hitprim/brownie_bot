import logging
from contextlib import asynccontextmanager

from aiogram.types import Update
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.bot.setup import get_bot, get_dispatcher
from src.config import settings
from src.db.session import dispose_engine

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("domovoy")


@asynccontextmanager
async def lifespan(app: FastAPI):
    bot = get_bot()
    await bot.set_webhook(
        url=settings.webhook_url,
        secret_token=settings.webhook_secret,
        drop_pending_updates=True,
        allowed_updates=["message"],
    )
    logger.info("Webhook set: %s", settings.webhook_url)
    yield
    await bot.delete_webhook()
    await bot.session.close()
    await dispose_engine()
    logger.info("Shutdown complete")


app = FastAPI(title="Домовой", lifespan=lifespan)


@app.post("/webhook")
async def webhook(request: Request):
    if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != settings.webhook_secret:
        return JSONResponse({"error": "unauthorized"}, status_code=401)

    bot = get_bot()
    dp = get_dispatcher()
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}


@app.get("/health")
async def health():
    return {"status": "ok", "service": "domovoy"}
