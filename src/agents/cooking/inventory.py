import logging

from src.agents.state import AgentState
from src.llm import LLMMessage, get_llm
from src.llm.prompts import load_prompt

logger = logging.getLogger(__name__)


async def inventory_node(state: AgentState) -> AgentState:
    """Извлекает список продуктов из текста."""
    llm = get_llm()
    messages = [
        LLMMessage(role="system", content=load_prompt("cooking/inventory")),
        LLMMessage(role="user", content=state["text"]),
    ]
    result = await llm.complete_json(messages)
    state["inventory"] = {
        "ingredients": result.get("ingredients", []),
        "approximate_quantities": result.get("approximate_quantities", {}),
        "missing_info": result.get("missing_info", []),
    }
    logger.info("Inventory: %d ingredients", len(state["inventory"]["ingredients"]))
    return state
