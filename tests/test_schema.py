"""Tests for biopulse.model.schema Pydantic models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from biopulse.model.schema import Edge, Event, EventStream, Graph, Node, Scene

# ---------------------------------------------------------------------------
# Node
# ---------------------------------------------------------------------------


def test_node_minimal() -> None:
    n = Node(id="STAT3")
    assert n.id == "STAT3"
    assert n.group is None


def test_node_with_group() -> None:
    n = Node(id="STAT3", group="TF")
    assert n.group == "TF"


def test_node_empty_id_rejected() -> None:
    with pytest.raises(ValidationError):
        Node(id="")


def test_node_extra_field_rejected() -> None:
    with pytest.raises(ValidationError):
        Node.model_validate({"id": "X", "weight": 0.5})


# ---------------------------------------------------------------------------
# Edge
# ---------------------------------------------------------------------------


def test_edge_activation() -> None:
    e = Edge(source="A", target="B", type="activation")
    assert e.type == "activation"


def test_edge_inhibition() -> None:
    e = Edge(source="A", target="B", type="inhibition")
    assert e.type == "inhibition"


def test_edge_unknown_type_rejected() -> None:
    with pytest.raises(ValidationError):
        Edge.model_validate({"source": "A", "target": "B", "type": "phosphorylation"})


def test_edge_empty_source_rejected() -> None:
    with pytest.raises(ValidationError):
        Edge(source="", target="B", type="activation")


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------


def test_graph_valid() -> None:
    g = Graph.model_validate(
        {
            "nodes": [{"id": "A"}, {"id": "B"}],
            "edges": [{"source": "A", "target": "B", "type": "activation"}],
        }
    )
    assert len(g.nodes) == 2
    assert len(g.edges) == 1


def test_graph_no_edges() -> None:
    g = Graph.model_validate({"nodes": [{"id": "A"}]})
    assert g.edges == []


def test_graph_duplicate_node_id_rejected() -> None:
    with pytest.raises(ValidationError, match="duplicate node id"):
        Graph.model_validate({"nodes": [{"id": "A"}, {"id": "A"}]})


def test_graph_edge_unknown_source_rejected() -> None:
    with pytest.raises(ValidationError, match="edge source"):
        Graph.model_validate(
            {
                "nodes": [{"id": "B"}],
                "edges": [{"source": "GHOST", "target": "B", "type": "activation"}],
            }
        )


def test_graph_edge_unknown_target_rejected() -> None:
    with pytest.raises(ValidationError, match="edge target"):
        Graph.model_validate(
            {
                "nodes": [{"id": "A"}],
                "edges": [{"source": "A", "target": "GHOST", "type": "activation"}],
            }
        )


# ---------------------------------------------------------------------------
# Event
# ---------------------------------------------------------------------------


def test_event_valid() -> None:
    e = Event(t=1.5, node="STAT3", state=1)
    assert e.t == 1.5
    assert e.state == 1


def test_event_negative_t_rejected() -> None:
    with pytest.raises(ValidationError):
        Event(t=-0.1, node="X", state=0)


def test_event_zero_t_allowed() -> None:
    e = Event(t=0.0, node="X", state=1)
    assert e.t == 0.0


def test_event_extra_field_rejected() -> None:
    with pytest.raises(ValidationError):
        Event.model_validate({"t": 1.0, "node": "X", "state": 1, "extra": True})


# ---------------------------------------------------------------------------
# EventStream (wire envelope)
# ---------------------------------------------------------------------------


def test_event_stream_envelope() -> None:
    es = EventStream.model_validate({"events": [{"t": 0.0, "node": "X", "state": 1}]})
    assert len(es.events) == 1


def test_event_stream_empty() -> None:
    es = EventStream.model_validate({"events": []})
    assert es.events == []


# ---------------------------------------------------------------------------
# Scene
# ---------------------------------------------------------------------------


def test_scene_valid() -> None:
    scene = Scene.model_validate(
        {
            "graph": {
                "nodes": [{"id": "IL6"}, {"id": "STAT3"}],
                "edges": [{"source": "IL6", "target": "STAT3", "type": "activation"}],
            },
            "events": [
                {"t": 0.0, "node": "IL6", "state": 1},
                {"t": 0.5, "node": "STAT3", "state": 1},
            ],
        }
    )
    assert len(scene.graph.nodes) == 2
    assert len(scene.events) == 2


def test_scene_event_unknown_node_rejected() -> None:
    with pytest.raises(ValidationError, match="unknown node"):
        Scene.model_validate(
            {
                "graph": {"nodes": [{"id": "A"}]},
                "events": [{"t": 0.0, "node": "GHOST", "state": 1}],
            }
        )


def test_scene_no_events() -> None:
    scene = Scene.model_validate({"graph": {"nodes": [{"id": "A"}]}})
    assert scene.events == []
