import logging

from src.llm import LLMMessage, get_llm
from src.llm.prompts import load_prompt

logger = logging.getLogger(__name__)


async def run_followup(
    text: str,
    *,
    domain: str,
    history: list[dict[str, str]] | None = None,
) -> str:
    """Контекстный follow-up в уже идущем диалоге (кулинария или быт).

    В отличие от полного пайплайна, не определяет домен и не диагностирует заново —
    отвечает на уточняющий вопрос в контексте предыдущих сообщений.
    """
    prompt_name = "home/followup" if domain == "home" else "cooking/followup"
    history = history or []
    history_text = "\n".join(f"{m['role']}: {m['content']}" for m in history)

    context = f"Контекст диалога:\n{history_text}\n\nНовый вопрос: {text}"
    messages = [
        LLMMessage(role="system", content=load_prompt(prompt_name)),
        LLMMessage(role="user", content=context),
    ]
    return await get_llm().complete(messages, temperature=0.4)
