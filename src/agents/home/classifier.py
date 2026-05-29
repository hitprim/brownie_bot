import logging

from src.agents.state import AgentState
from src.llm import LLMMessage, get_llm
from src.llm.prompts import load_prompt

logger = logging.getLogger(__name__)

VALID_CATEGORIES = {
    "plumbing",
    "electrical",
    "appliances",
    "cleaning",
    "structure",
    "legal",
    "other",
}


async def classifier_node(state: AgentState) -> AgentState:
    """Определяет категорию и срочность бытовой проблемы."""
    llm = get_llm()
    messages = [
        LLMMessage(role="system", content=load_prompt("home/classifier")),
        LLMMessage(role="user", content=state["text"]),
    ]
    result = await llm.complete_json(messages)

    category = result.get("category", "other")
    if category not in VALID_CATEGORIES:
        category = "other"
    urgency = result.get("urgency", "medium")
    if urgency not in ("high", "medium", "low"):
        urgency = "medium"

    state["category"] = category
    state["urgency"] = urgency
    logger.info("Classifier: category=%s urgency=%s", category, urgency)
    return state
