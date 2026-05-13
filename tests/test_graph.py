"""Tests for biopulse.model.graph.Graph wrapper."""

from __future__ import annotations

from biopulse.model.graph import Graph
from biopulse.model.schema import Graph as GraphSchema


def _make_schema(
    nodes: list[dict[str, str]], edges: list[dict[str, str]] | None = None
) -> GraphSchema:
    data: dict[str, list[dict[str, str]]] = {"nodes": nodes}
    if edges:
        data["edges"] = edges
    return GraphSchema.model_validate(data)


def test_build_nodes() -> None:
    g = Graph(_make_schema([{"id": "A"}, {"id": "B"}]))
    assert len(g) == 2
    assert "A" in g
    assert "B" in g


def test_build_edges() -> None:
    schema = _make_schema(
        [{"id": "A"}, {"id": "B"}],
        [{"source": "A", "target": "B", "type": "activation"}],
    )
    g = Graph(schema)
    edges = list(g.digraph.edges(data=True))
    assert len(edges) == 1
    src, tgt, data = edges[0]
    assert src == "A"
    assert tgt == "B"
    assert data["type"] == "activation"


def test_node_group_attribute() -> None:
    schema = _make_schema([{"id": "STAT3", "group": "TF"}])
    g = Graph(schema)
    assert g.digraph.nodes["STAT3"]["group"] == "TF"


def test_node_without_group_has_no_attr() -> None:
    schema = _make_schema([{"id": "X"}])
    g = Graph(schema)
    assert "group" not in g.digraph.nodes["X"]


def test_node_ids_order() -> None:
    schema = _make_schema([{"id": "C"}, {"id": "A"}, {"id": "B"}])
    g = Graph(schema)
    assert g.node_ids == ["C", "A", "B"]


def test_contains_unknown_node() -> None:
    g = Graph(_make_schema([{"id": "A"}]))
    assert "GHOST" not in g


def test_repr() -> None:
    g = Graph(
        _make_schema(
            [{"id": "A"}, {"id": "B"}],
            [{"source": "A", "target": "B", "type": "inhibition"}],
        )
    )
    assert "nodes=2" in repr(g)
    assert "edges=1" in repr(g)


def test_schema_roundtrip() -> None:
    schema = _make_schema(
        [{"id": "IL6", "group": "ligand"}, {"id": "STAT3"}],
        [{"source": "IL6", "target": "STAT3", "type": "activation"}],
    )
    g = Graph(schema)
    assert g.schema is schema
