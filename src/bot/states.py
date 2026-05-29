from aiogram.fsm.state import State, StatesGroup


class ConversationStates(StatesGroup):
    idle = State()  # начальное состояние
    clarifying_domain = State()  # уточняем домен (Router вернул unclear)
    cooking_clarifying = State()  # уточняем кулинарный запрос
    cooking_answering = State()  # ответили рецептом, ждём follow-up (замены)
    home_diagnosing = State()  # диагностируем бытовую проблему
    home_answering = State()  # ответили решением, ждём follow-up
