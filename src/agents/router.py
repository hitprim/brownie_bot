import logging

from src.agents.state import AgentState
from src.llm import LLMMessage, get_llm
from src.llm.prompts import load_prompt

logger = logging.getLogger(__name__)


async def router_node(state: AgentState) -> AgentState:
    """Определяет домен запроса. Возвращает domain + confidence (+ вопрос если unclear)."""
    llm = get_llm()
    messages = [
        LLMMessage(role="system", content=load_prompt("router")),
        LLMMessage(role="user", content=state["text"]),
    ]
    result = await llm.complete_json(messages)

    domain = result.get("domain", "unclear")
    if domain not in ("cooking", "home", "unclear"):
        domain = "unclear"

    state["domain"] = domain
    state["confidence"] = float(result.get("confidence", 0.0))

    if domain == "unclear":
        state["clarifying_question"] = result.get("clarifying_question") or (
            "Уточните, пожалуйста: это вопрос про готовку/еду или про бытовую ситуацию дома?"
        )
        state["response"] = state["clarifying_question"]

    logger.info("Router: domain=%s confidence=%.2f", domain, state["confidence"])
    return state


def route_by_domain(state: AgentState) -> str:
    """Условный переход после роутера."""
    return state["domain"]
