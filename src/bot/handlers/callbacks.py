import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards import CB_FB_DOWN, CB_FB_UP, CB_MORE_RECIPE, CB_NEW, CB_SWAP
from src.bot.processing import process_message
from src.bot.states import ConversationStates
from src.db.models import User
from src.domain.user import UserDTO
from src.services.conversation_service import ConversationService
from src.services.event_service import EventService

logger = logging.getLogger("domovoy.bot")

router = Router(name="callbacks")


@router.callback_query(F.data.in_({CB_FB_UP, CB_FB_DOWN}))
async def on_feedback(
    callback: CallbackQuery,
    state: FSMContext,
    user: User,
    session: AsyncSession,
) -> None:
    rating = "up" if callback.data == CB_FB_UP else "down"
    data = await state.get_data()
    await EventService(session).log(
        user_id=user.id,
        event_type="feedback",
        domain=data.get("domain"),
        metadata={"rating": rating},
    )
    # убираем кнопки, чтобы не голосовали дважды
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        logger.debug("Could not edit reply markup", exc_info=True)
    await callback.answer("Спасибо за оценку!" if rating == "up" else "Спасибо, учту!")


@router.callback_query(F.data == CB_NEW)
async def on_new_request(
    callback: CallbackQuery,
    state: FSMContext,
    user: User,
    session: AsyncSession,
) -> None:
    await ConversationService(session).reset(user.id)
    await state.set_state(ConversationStates.idle)
    await callback.message.answer("Слушаю. Что у вас?")
    await callback.answer()


@router.callback_query(F.data == CB_SWAP)
async def on_swap(callback: CallbackQuery) -> None:
    await callback.message.answer(
        "Напишите, какого продукта нет — подберу замену под этот рецепт."
    )
    await callback.answer()


@router.callback_query(F.data == CB_MORE_RECIPE)
async def on_more_recipe(
    callback: CallbackQuery,
    state: FSMContext,
    user: User,
    user_dto: UserDTO,
    session: AsyncSession,
) -> None:
    await callback.answer()
    await process_message(
        callback.message,
        text="Предложи ещё один вариант рецепта из тех же продуктов.",
        user=user,
        user_dto=user_dto,
        state=state,
        session=session,
    )
