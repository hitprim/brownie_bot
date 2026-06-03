import logging

from src.agents.state import AgentState
from src.llm import LLMMessage, get_llm
from src.llm.prompts import load_prompt

logger = logging.getLogger(__name__)


async def pro_node(state: AgentState) -> AgentState:
    """Когда и какой специалист нужен (или что справишься сам)."""
    llm = get_llm()
    context = (
        f"Категория: {state.get('category', 'other')}\n"
        f"Проблема: {state['text']}"
    )
    system = load_prompt("home/pro")
    if state.get("memory_facts"):
        system = f"{system}\n\n{state['memory_facts']}"
    messages = [
        LLMMessage(role="system", content=system),
        LLMMessage(role="user", content=context),
    ]
    text = await llm.complete(messages, temperature=0.3)
    return {"pro": text}
