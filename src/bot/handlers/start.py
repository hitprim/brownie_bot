from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src.bot.states import ConversationStates
from src.db.models import User
from src.db.session import async_session_factory
from src.services.conversation_service import ConversationService

router = Router(name="start")

WELCOME = (
    "Привет! Я Домовой 🏠\n\n"
    "Помогаю по двум темам:\n"
    "🍳 <b>Кулинария</b> — скажите что есть в холодильнике, подберу рецепты.\n"
    "🔧 <b>Быт</b> — опишите проблему (кран течёт, пятно, что-то сломалось), "
    "подскажу что делать.\n\n"
    "Можно писать текстом или присылать голосовые. Просто расскажите, что у вас случилось."
)

HELP = (
    "Как пользоваться:\n"
    "• Кулинария: «есть курица, картошка и лук — что приготовить за 30 минут?»\n"
    "• Быт: «капает кран на кухне» или «как вывести пятно от вина»\n\n"
    "Команды:\n"
    "/start — начать заново\n"
    "/help — эта справка\n"
    "/reset — сбросить текущий диалог"
)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, user: User) -> None:
    async with async_session_factory() as session:
        await ConversationService(session).reset(user.id)
    await state.set_state(ConversationStates.idle)
    await message.answer(WELCOME)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(HELP)


@router.message(Command("reset"))
async def cmd_reset(message: Message, state: FSMContext, user: User) -> None:
    async with async_session_factory() as session:
        await ConversationService(session).reset(user.id)
    await state.set_state(ConversationStates.idle)
    await message.answer("Начнём с чистого листа. Что у вас?")
