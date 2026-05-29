from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src.bot.processing import process_message
from src.db.models import User
from src.domain.user import UserDTO

router = Router(name="text")


@router.message(F.text & ~F.text.startswith("/"))
async def handle_text(
    message: Message,
    state: FSMContext,
    user: User,
    user_dto: UserDTO,
) -> None:
    await process_message(
        message,
        text=message.text or "",
        user=user,
        user_dto=user_dto,
        state=state,
        is_voice=False,
    )
