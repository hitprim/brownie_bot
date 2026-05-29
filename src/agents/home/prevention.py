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
    messages = [
        LLMMessage(role="system", content=load_prompt("home/prevention")),
        LLMMessage(role="user", content=context),
    ]
    parts = state.setdefault("home_parts", {})
    parts["prevention"] = await llm.complete(messages, temperature=0.4)
    return state


async def assemble_home_node(state: AgentState) -> AgentState:
    """Собирает DIY + Pro + Prevention в один ответ пользователю."""
    parts = state.get("home_parts", {})
    blocks: list[str] = []
    if parts.get("diy"):
        blocks.append(parts["diy"].strip())
    if parts.get("pro"):
        blocks.append(parts["pro"].strip())
    if parts.get("prevention"):
        blocks.append(parts["prevention"].strip())
    state["response"] = "\n\n".join(blocks)
    return state
