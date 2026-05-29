import logging

from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src.agents.graph import run_agents, run_cooking_followup
from src.bot.formatting import telegram_html
from src.bot.states import ConversationStates
from src.db.models import User
from src.db.session import async_session_factory
from src.domain.user import UserDTO
from src.services.conversation_service import ConversationService

logger = logging.getLogger("domovoy.bot")

GENERIC_ERROR = (
    "Что-то пошло не так на моей стороне. Попробуйте ещё раз чуть позже 🙏"
)


async def process_message(
    message: Message,
    *,
    text: str,
    user: User,
    user_dto: UserDTO,
    state: FSMContext,
    is_voice: bool = False,
) -> None:
    """Единая обработка текста (и транскрипции голоса) через multi-agent граф."""
    if not text.strip():
        await message.answer("Не расслышал. Напишите или скажите ещё раз, пожалуйста.")
        return

    user_id = user.id
    current = await state.get_state()

    async with async_session_factory() as session:
        conv = ConversationService(session)
        await conv.record_user_message(user_id, text, is_voice=is_voice)
        history = await conv.history(user_id, limit=10)

    try:
        if current == ConversationStates.cooking_answering.state:
            response = await run_cooking_followup(text, history=history)
            next_state = ConversationStates.cooking_answering
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
                async with async_session_factory() as session:
                    await ConversationService(session).set_domain(user_id, domain)
    except Exception:
        logger.exception("Agent pipeline failed for user=%s", user_id)
        await message.answer(GENERIC_ERROR)
        return

    if not response:
        response = GENERIC_ERROR

    await state.set_state(next_state)
    async with async_session_factory() as session:
        await ConversationService(session).record_assistant_message(user_id, response)

    await message.answer(telegram_html(response))
