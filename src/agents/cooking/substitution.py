import logging

from src.agents.state import AgentState
from src.llm import LLMMessage, get_llm
from src.llm.prompts import load_prompt

logger = logging.getLogger(__name__)


async def substitution_node(state: AgentState) -> AgentState:
    """Подбирает замены недостающим ингредиентам в контексте диалога."""
    llm = get_llm()
    history = state.get("history", [])
    history_text = "\n".join(f"{m['role']}: {m['content']}" for m in history)

    context = (
        f"Контекст диалога:\n{history_text}\n\n"
        f"Запрос на замену: {state['text']}"
    )

    messages = [
        LLMMessage(role="system", content=load_prompt("cooking/substitution")),
        LLMMessage(role="user", content=context),
    ]
    state["response"] = await llm.complete(messages, temperature=0.4)
    return state
