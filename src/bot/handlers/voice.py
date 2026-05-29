import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src.bot.processing import process_message
from src.bot.setup import get_bot
from src.db.models import User
from src.domain.user import UserDTO
from src.stt import get_stt
from src.stt.groq_whisper import STTError

logger = logging.getLogger("domovoy.bot")

router = Router(name="voice")


@router.message(F.voice)
async def handle_voice(
    message: Message,
    state: FSMContext,
    user: User,
    user_dto: UserDTO,
) -> None:
    bot = get_bot()
    await message.bot.send_chat_action(message.chat.id, "typing")

    file = await bot.get_file(message.voice.file_id)
    buffer = await bot.download_file(file.file_path)
    audio_data = buffer.read()

    try:
        transcript = await get_stt().transcribe(audio_data, language="ru")
    except STTError:
        logger.exception("STT failed for user=%s", user.id)
        await message.answer(
            "Не получилось распознать голос. Попробуйте ещё раз или напишите текстом."
        )
        return

    await process_message(
        message,
        text=transcript,
        user=user,
        user_dto=user_dto,
        state=state,
        is_voice=True,
    )
