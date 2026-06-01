from functools import lru_cache
from typing import Any

from langgraph.graph import END, StateGraph

from src.agents.cooking.inventory import inventory_node
from src.agents.cooking.preference import preference_node
from src.agents.cooking.recipe import recipe_node
from src.agents.home.classifier import classifier_node
from src.agents.home.diagnosis import diagnosis_node, route_after_diagnosis
from src.agents.home.diy import diy_node
from src.agents.home.prevention import assemble_home_node, prevention_node
from src.agents.home.pro import pro_node
from src.agents.router import route_by_domain, router_node
from src.agents.state import AgentState


def _build_main_graph():
    """Главный граф: router → cooking / home / unclear."""
    g = StateGraph(AgentState)

    g.add_node("router", router_node)

    g.add_node("inventory", inventory_node)
    g.add_node("preference", preference_node)
    g.add_node("recipe", recipe_node)

    g.add_node("classifier", classifier_node)
    g.add_node("diagnosis", diagnosis_node)
    g.add_node("diy", diy_node)
    g.add_node("pro", pro_node)
    g.add_node("prevention", prevention_node)
    g.add_node("assemble_home", assemble_home_node)

    g.set_entry_point("router")
    g.add_conditional_edges(
        "router",
        route_by_domain,
        {"cooking": "inventory", "home": "classifier", "unclear": END},
    )

    g.add_edge("inventory", "preference")
    g.add_edge("preference", "recipe")
    g.add_edge("recipe", END)

    g.add_edge("classifier", "diagnosis")
    # fan-out: после диагностики три агента работают параллельно
    g.add_conditional_edges(
        "diagnosis",
        route_after_diagnosis,
        ["diy", "pro", "prevention", END],
    )
    # fan-in: assemble_home ждёт завершения всех трёх
    g.add_edge("diy", "assemble_home")
    g.add_edge("pro", "assemble_home")
    g.add_edge("prevention", "assemble_home")
    g.add_edge("assemble_home", END)

    return g.compile()


@lru_cache
def get_graph():
    return _build_main_graph()


async def run_agents(
    text: str,
    *,
    user_prefs: dict[str, Any] | None = None,
    history: list[dict[str, str]] | None = None,
) -> AgentState:
    """Прогоняет запрос через главный граф. Возвращает финальный state."""
    graph = get_graph()
    initial: AgentState = {
        "text": text,
        "user_prefs": user_prefs or {},
        "history": history or [],
    }
    return await graph.ainvoke(initial)
