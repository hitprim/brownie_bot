import logging

from src.agents.state import AgentState
from src.llm import LLMMessage, get_llm
from src.llm.prompts import load_prompt

logger = logging.getLogger(__name__)


async def prevention_node(state: AgentState) -> AgentState:
    """Короткий совет как избежать повторения. Идёт в конце ответа."""
    llm = get_llm()
    context = (
        f"Категория: {state.get('category', 'other')}\n"
        f"Проблема: {state['text']}"
    )
    system = load_prompt("home/prevention")
    if state.get("memory_facts"):
        system = f"{system}\n\n{state['memory_facts']}"
    messages = [
        LLMMessage(role="system", content=system),
        LLMMessage(role="user", content=context),
    ]
    text = await llm.complete(messages, temperature=0.4)
    return {"prevention": text}


async def assemble_home_node(state: AgentState) -> AgentState:
    """Собирает DIY + Pro + Prevention (заполненные параллельно) в один ответ."""
    blocks = [
        state.get("diy", "").strip(),
        state.get("pro", "").strip(),
        state.get("prevention", "").strip(),
    ]
    return {"response": "\n\n".join(b for b in blocks if b)}
