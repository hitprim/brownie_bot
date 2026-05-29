from src.agents.graph import get_graph


def test_graph_compiles() -> None:
    graph = get_graph()
    assert graph is not None


def test_graph_has_expected_nodes() -> None:
    graph = get_graph()
    nodes = set(graph.get_graph().nodes.keys())
    expected = {
        "router",
        "inventory",
        "preference",
        "recipe",
        "classifier",
        "diagnosis",
        "diy",
        "pro",
        "prevention",
        "assemble_home",
    }
    assert expected.issubset(nodes)
