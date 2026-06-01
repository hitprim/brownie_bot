import logging

from langgraph.graph import END

from src.agents.state import AgentState
from src.llm import LLMMessage, get_llm
from src.llm.prompts import load_prompt

logger = logging.getLogger(__name__)


async def diagnosis_node(state: AgentState) -> AgentState:
    """Решает, нужен ли один уточняющий вопрос перед выдачей решения.

    При urgency=high пропускаем диагностику — сразу к решению (экстренные действия).
    """
    if state.get("urgency") == "high":
        state["needs_clarification"] = False
        return state

    llm = get_llm()
    history = state.get("history", [])
    history_text = "\n".join(f"{m['role']}: {m['content']}" for m in history)
    context = (
        f"Категория: {state.get('category', 'other')}\n"
        f"Контекст диалога:\n{history_text}\n\n"
        f"Сообщение: {state['text']}"
    )

    messages = [
        LLMMessage(role="system", content=load_prompt("home/diagnosis")),
        LLMMessage(role="user", content=context),
    ]
    result = await llm.complete_json(messages)

    needs = bool(result.get("needs_clarification", False))
    state["needs_clarification"] = needs
    if needs:
        question = result.get("question") or "Опишите проблему чуть подробнее, пожалуйста."
        state["clarifying_question"] = question
        state["response"] = question
    logger.info("Diagnosis: needs_clarification=%s", needs)
    return state


def route_after_diagnosis(state: AgentState):
    """Если нужен вопрос — заканчиваем, иначе запускаем DIY/Pro/Prevention параллельно."""
    if state.get("needs_clarification"):
        return END
    return ["diy", "pro", "prevention"]
