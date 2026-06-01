import logging

from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.utils.chat_action import ChatActionSender
from sqlalchemy.ext.asyncio import AsyncSession

from src.agents.followup import run_followup
from src.agents.graph import run_agents
from src.bot.formatting import split_for_telegram, telegram_html
from src.bot.keyboards import answer_keyboard
from src.bot.states import ConversationStates
from src.db.models import User
from src.domain.user import UserDTO
from src.services.conversation_service import ConversationService

logger = logging.getLogger("domovoy.bot")

GENERIC_ERROR = (
    "Что-то пошло не так на моей стороне. Попробуйте ещё раз чуть позже 🙏"
)

_FOLLOWUP_STATES = {
    ConversationStates.cooking_answering.state: "cooking",
    ConversationStates.home_answering.state: "home",
}


async def process_message(
    message: Message,
    *,
    text: str,
    user: User,
    user_dto: UserDTO,
    state: FSMContext,
    session: AsyncSession,
    is_voice: bool = False,
) -> None:
    """Единая обработка текста (и транскрипции голоса) через multi-agent граф."""
    if not text.strip():
        await message.answer("Не расслышал. Напишите или скажите ещё раз, пожалуйста.")
        return

    user_id = user.id
    current = await state.get_state()
    conv = ConversationService(session)
    await conv.record_user_message(user_id, text, is_voice=is_voice)
    history = await conv.history(user_id, limit=10)

    try:
        async with ChatActionSender.typing(bot=message.bot, chat_id=message.chat.id):
            if current in _FOLLOWUP_STATES:
                domain = _FOLLOWUP_STATES[current]
                response = (await run_followup(text, domain=domain, history=history)).strip()
                next_state = (
                    ConversationStates.home_answering
                    if domain == "home"
                    else ConversationStates.cooking_answering
                )
            else:
                result = await run_agents(
                    text,
                    user_prefs=user_dto.preferences.model_dump(),
                    history=history,
                )
                response = result.get("response", "").strip()
                domain = result.get("domain", "unclear")

                if domain == "unclear":
                    next_state = ConversationStates.clarifying_domain
                elif domain == "home" and result.get("needs_clarification"):
                    next_state = ConversationStates.home_diagnosing
                elif domain == "home":
                    next_state = ConversationStates.home_answering
                else:  # cooking
                    next_state = ConversationStates.cooking_answering

                if domain in ("cooking", "home"):
                    await conv.set_domain(user_id, domain)
    except Exception:
        logger.exception("Agent pipeline failed for user=%s", user_id)
        await message.answer(GENERIC_ERROR)
        return

    if not response:
        response = GENERIC_ERROR

    await state.set_state(next_state)
    await state.update_data(domain=domain)
    await conv.record_assistant_message(user_id, response)

    answering = next_state in (
        ConversationStates.cooking_answering,
        ConversationStates.home_answering,
    )
    keyboard = answer_keyboard(domain) if answering else None

    chunks = split_for_telegram(telegram_html(response))
    for i, chunk in enumerate(chunks):
        await message.answer(
            chunk,
            reply_markup=keyboard if i == len(chunks) - 1 else None,
        )
