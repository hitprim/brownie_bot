from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    """State, передаётся между узлами графа LangGraph."""

    text: str
    user_prefs: dict[str, Any]
    history: list[dict[str, str]]
    memory_facts: str  # факты о пользователе из mem0 для подмешивания в промпт

    domain: str  # "cooking" | "home" | "unclear"
    confidence: float

    inventory: dict[str, Any]
    preferences: dict[str, Any]

    category: str
    urgency: str  # "high" | "medium" | "low"
    needs_clarification: bool
    # части бытового ответа — заполняются параллельно (каждый узел пишет свой ключ)
    diy: str
    pro: str
    prevention: str

    clarifying_question: str | None
    response: str
