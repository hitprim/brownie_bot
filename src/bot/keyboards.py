from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

# callback data
CB_MORE_RECIPE = "act:more_recipe"
CB_SWAP = "act:swap"
CB_NEW = "act:new"
CB_FB_UP = "fb:up"
CB_FB_DOWN = "fb:down"


def _feedback_row(builder: InlineKeyboardBuilder) -> None:
    builder.row(
        InlineKeyboardButton(text="👍", callback_data=CB_FB_UP),
        InlineKeyboardButton(text="👎", callback_data=CB_FB_DOWN),
    )


def answer_keyboard(domain: str) -> InlineKeyboardMarkup:
    """Кнопки под финальным ответом: действия по домену + оценка."""
    builder = InlineKeyboardBuilder()
    if domain == "cooking":
        builder.row(
            InlineKeyboardButton(text="🍽 Ещё рецепт", callback_data=CB_MORE_RECIPE),
            InlineKeyboardButton(text="🔄 Заменить продукт", callback_data=CB_SWAP),
        )
    builder.row(InlineKeyboardButton(text="✨ Новый запрос", callback_data=CB_NEW))
    _feedback_row(builder)
    return builder.as_markup()
