import html
import re

_BOLD_STARS = re.compile(r"\*\*(.+?)\*\*", re.S)
_BOLD_UNDERSCORES = re.compile(r"__(.+?)__", re.S)
_HEADING = re.compile(r"(?m)^[ \t]{0,3}#{1,6}[ \t]*(.+?)[ \t]*$")
_ITALIC = re.compile(r"(?<![*\w])\*(?!\s)(.+?)(?<!\s)\*(?!\*)", re.S)
_BULLET = re.compile(r"(?m)^([ \t]*)[*+]\s+")


def telegram_html(text: str) -> str:
    """Конвертирует Markdown-вывод LLM в Telegram-совместимый HTML.

    Telegram parse_mode=HTML не понимает '**' и '#'. Экранируем спецсимволы,
    затем превращаем разметку в поддерживаемые теги (<b>, <i>).
    """
    text = html.escape(text, quote=False)
    text = _BOLD_STARS.sub(r"<b>\1</b>", text)
    text = _BOLD_UNDERSCORES.sub(r"<b>\1</b>", text)
    text = _HEADING.sub(r"<b>\1</b>", text)
    text = _ITALIC.sub(r"<i>\1</i>", text)
    # markdown-маркеры списка '* '/'+ ' → обычное тире
    text = _BULLET.sub(r"\1• ", text)
    return text
