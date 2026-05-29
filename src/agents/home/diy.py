import logging

from src.agents.state import AgentState
from src.llm import LLMMessage, get_llm
from src.llm.prompts import load_prompt

logger = logging.getLogger(__name__)


async def diy_node(state: AgentState) -> AgentState:
    """Пошаговое решение для новичка. Самый важный агент бытового пайплайна."""
    llm = get_llm()
    context = (
        f"Категория: {state.get('category', 'other')}\n"
        f"Срочность: {state.get('urgency', 'medium')}\n"
        f"Проблема: {state['text']}"
    )
    messages = [
        LLMMessage(role="system", content=load_prompt("home/diy")),
        LLMMessage(role="user", content=context),
    ]
    parts = state.setdefault("home_parts", {})
    parts["diy"] = await llm.complete(messages, temperature=0.4)
    return state
