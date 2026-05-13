"""Tests for biopulse.layouts.*"""

from __future__ import annotations

from biopulse.layouts.forceatlas import ForceAtlasLayout
from biopulse.model.graph import Graph
from biopulse.model.schema import Graph as GraphSchema


def _graph(*node_ids: str, edges: list[tuple[str, str, str]] | None = None) -> Graph:
    nodes = [{"id": nid} for nid in node_ids]
    edge_dicts = [{"source": s, "target": t, "type": et} for s, t, et in edges] if edges else []
    return Graph(GraphSchema.model_validate({"nodes": nodes, "edges": edge_dicts}))


# ---------------------------------------------------------------------------
# ForceAtlasLayout
# ---------------------------------------------------------------------------


def test_all_nodes_have_positions() -> None:
    g = _graph("A", "B", "C")
    pos = ForceAtlasLayout().compute(g)
    assert set(pos) == {"A", "B", "C"}


def test_positions_are_2d_floats() -> None:
    g = _graph("X", "Y")
    pos = ForceAtlasLayout().compute(g)
    for xy in pos.values():
        assert len(xy) == 2
        assert isinstance(xy[0], float)
        assert isinstance(xy[1], float)


def test_reproducible_with_seed() -> None:
    g = _graph("A", "B", "C", edges=[("A", "B", "activation"), ("B", "C", "inhibition")])
    layout = ForceAtlasLayout(seed=0)
    pos1 = layout.compute(g)
    pos2 = layout.compute(g)
    assert pos1 == pos2


def test_different_seeds_differ() -> None:
    g = _graph("A", "B", "C", "D")
    pos_a = ForceAtlasLayout(seed=1).compute(g)
    pos_b = ForceAtlasLayout(seed=99).compute(g)
    # Very unlikely to be identical with different seeds on 4+ nodes
    assert pos_a != pos_b


def test_single_node() -> None:
    g = _graph("OnlyNode")
    pos = ForceAtlasLayout().compute(g)
    assert "OnlyNode" in pos
    assert len(pos) == 1


def test_empty_graph_returns_empty() -> None:
    g = Graph(GraphSchema.model_validate({"nodes": []}))
    pos = ForceAtlasLayout().compute(g)
    assert pos == {}


def test_disconnected_graph() -> None:
    g = _graph("A", "B", "C", "D")
    pos = ForceAtlasLayout(seed=7).compute(g)
    assert len(pos) == 4


def test_layout_positions_finite() -> None:
    g = _graph("P", "Q", "R", edges=[("P", "Q", "activation"), ("Q", "R", "activation")])
    pos = ForceAtlasLayout().compute(g)
    import math

    for xy in pos.values():
        assert math.isfinite(xy[0]) and math.isfinite(xy[1])
