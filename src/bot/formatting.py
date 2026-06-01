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


TELEGRAM_LIMIT = 4096


def split_for_telegram(text: str, limit: int = TELEGRAM_LIMIT) -> list[str]:
    """Режет длинный текст на части под лимит Telegram, по границам абзацев/строк.

    Простые инлайн-теги (<b>, <i>) не переносятся между абзацами, поэтому
    деление по '\\n\\n' и '\\n' не разрывает разметку.
    """
    if len(text) <= limit:
        return [text]

    chunks: list[str] = []
    current = ""
    for block in text.split("\n\n"):
        candidate = f"{current}\n\n{block}" if current else block
        if len(candidate) <= limit:
            current = candidate
            continue
        if current:
            chunks.append(current)
            current = ""
        # сам блок длиннее лимита — режем по строкам
        if len(block) <= limit:
            current = block
            continue
        for line in block.split("\n"):
            cand = f"{current}\n{line}" if current else line
            if len(cand) <= limit:
                current = cand
            else:
                if current:
                    chunks.append(current)
                # строка всё ещё длиннее лимита — режем жёстко
                while len(line) > limit:
                    chunks.append(line[:limit])
                    line = line[limit:]
                current = line
    if current:
        chunks.append(current)
    return chunks
