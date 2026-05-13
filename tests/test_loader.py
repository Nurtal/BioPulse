"""Tests for biopulse.io.json_loader."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from biopulse.io.json_loader import load_events, load_graph, load_scene
from biopulse.model.events import EventStream
from biopulse.model.graph import Graph

EXAMPLES = Path(__file__).parent.parent / "examples" / "data"


# ---------------------------------------------------------------------------
# load_graph
# ---------------------------------------------------------------------------


def test_load_graph_example(tmp_path: Path) -> None:
    g = load_graph(EXAMPLES / "feedforward_loop.graph.json")
    assert isinstance(g, Graph)
    assert len(g) == 3
    assert "A" in g and "B" in g and "C" in g


def test_load_graph_returns_digraph_edges(tmp_path: Path) -> None:
    g = load_graph(EXAMPLES / "feedforward_loop.graph.json")
    assert g.digraph.has_edge("A", "B")
    assert g.digraph.has_edge("A", "C")
    assert g.digraph.has_edge("B", "C")


def test_load_graph_invalid_schema(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"nodes": [{"id": "A"}, {"id": "A"}]}))
    with pytest.raises(ValidationError):
        load_graph(bad)


def test_load_graph_missing_file() -> None:
    with pytest.raises(FileNotFoundError):
        load_graph("/nonexistent/path.json")


def test_load_graph_roundtrip(tmp_path: Path) -> None:
    data = {
        "nodes": [{"id": "X", "group": "g1"}, {"id": "Y"}],
        "edges": [{"source": "X", "target": "Y", "type": "inhibition"}],
    }
    p = tmp_path / "g.json"
    p.write_text(json.dumps(data))
    g = load_graph(p)
    assert g.digraph.edges["X", "Y"]["type"] == "inhibition"
    assert g.digraph.nodes["X"]["group"] == "g1"


# ---------------------------------------------------------------------------
# load_events
# ---------------------------------------------------------------------------


def test_load_events_example() -> None:
    es = load_events(EXAMPLES / "toggle.events.json")
    assert isinstance(es, EventStream)
    assert len(es) == 4


def test_load_events_sorted() -> None:
    es = load_events(EXAMPLES / "toggle.events.json")
    times = [e.t for e in es]
    assert times == sorted(times)


def test_load_events_invalid_negative_t(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"events": [{"t": -1.0, "node": "X", "state": 1}]}))
    with pytest.raises(ValidationError):
        load_events(bad)


def test_load_events_missing_file() -> None:
    with pytest.raises(FileNotFoundError):
        load_events("/nonexistent/events.json")


# ---------------------------------------------------------------------------
# load_scene
# ---------------------------------------------------------------------------


def test_load_scene_example() -> None:
    g, es = load_scene(EXAMPLES / "il6_stat3.scene.json")
    assert isinstance(g, Graph)
    assert isinstance(es, EventStream)
    assert len(g) == 4
    assert len(es) == 5


def test_load_scene_graph_correct() -> None:
    g, _ = load_scene(EXAMPLES / "il6_stat3.scene.json")
    assert "IL6" in g
    assert "STAT3" in g
    assert g.digraph.edges["JAK1", "STAT3"]["type"] == "activation"
    assert g.digraph.edges["SOCS3", "JAK1"]["type"] == "inhibition"


def test_load_scene_events_sorted() -> None:
    _, es = load_scene(EXAMPLES / "il6_stat3.scene.json")
    times = [e.t for e in es]
    assert times == sorted(times)


def test_load_scene_unknown_node_rejected(tmp_path: Path) -> None:
    bad = tmp_path / "bad_scene.json"
    bad.write_text(
        json.dumps(
            {
                "graph": {"nodes": [{"id": "A"}]},
                "events": [{"t": 0.0, "node": "GHOST", "state": 1}],
            }
        )
    )
    with pytest.raises(ValidationError, match="unknown node"):
        load_scene(bad)


def test_load_scene_missing_file() -> None:
    with pytest.raises(FileNotFoundError):
        load_scene("/nonexistent/scene.json")
