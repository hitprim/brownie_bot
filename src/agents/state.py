from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    """State, передаётся между узлами графа LangGraph."""

    text: str
    user_prefs: dict[str, Any]
    history: list[dict[str, str]]

    domain: str  # "cooking" | "home" | "unclear"
    confidence: float

    inventory: dict[str, Any]
    preferences: dict[str, Any]

    category: str
    urgency: str  # "high" | "medium" | "low"
    needs_clarification: bool
    home_parts: dict[str, str]

    clarifying_question: str | None
    response: str
