from src.agents.state import AgentState


async def preference_node(state: AgentState) -> AgentState:
    """Сводит предпочтения из БД с тем что есть в запросе.

    v0.1: preferences в БД не сохраняем, берём дефолты из user_prefs.
    """
    prefs = state.get("user_prefs", {})
    state["preferences"] = {
        "portions": prefs.get("default_portions", 2),
        "max_time_minutes": prefs.get("max_time_minutes"),
        "restrictions": prefs.get("dietary_restrictions", []),
        "disliked": prefs.get("disliked_ingredients", []),
        "skill_level": prefs.get("cooking_skill", "beginner"),
    }
    return state
