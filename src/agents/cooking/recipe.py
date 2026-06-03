import json
import logging

from src.agents.state import AgentState
from src.llm import LLMMessage, get_llm
from src.llm.prompts import load_prompt

logger = logging.getLogger(__name__)


async def recipe_node(state: AgentState) -> AgentState:
    """Генерирует 2-3 рецепта. Основной агент кулинарного пайплайна."""
    llm = get_llm()
    inventory = state.get("inventory", {})
    preferences = state.get("preferences", {})

    context = (
        f"Доступные продукты: {', '.join(inventory.get('ingredients', [])) or '(не указаны)'}\n"
        f"Предпочтения: {json.dumps(preferences, ensure_ascii=False)}\n"
        f"Исходный запрос: {state['text']}"
    )

    system = load_prompt("cooking/recipe")
    if state.get("memory_facts"):
        system = f"{system}\n\n{state['memory_facts']}"
    messages = [
        LLMMessage(role="system", content=system),
        LLMMessage(role="user", content=context),
    ]
    state["response"] = await llm.complete(messages, temperature=0.6)
    logger.info("Recipe generated (%d chars)", len(state["response"]))
    return state
