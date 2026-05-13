"""Tests for PlayWidget and biopulse.play() public API."""

from __future__ import annotations

import biopulse
from biopulse.core.renderer.widget import PlayWidget
from biopulse.io.json_loader import load_scene
from biopulse.model.events import EventStream
from biopulse.model.graph import Graph
from biopulse.model.schema import Event
from biopulse.model.schema import Graph as GraphSchema


def _make_graph(*node_ids: str, edges: list[tuple[str, str, str]] | None = None) -> Graph:
    nodes = [{"id": nid} for nid in node_ids]
    edge_dicts = [{"source": s, "target": t, "type": et} for s, t, et in edges] if edges else []
    return Graph(GraphSchema.model_validate({"nodes": nodes, "edges": edge_dicts}))


def _make_events(*pairs: tuple[float, str, int]) -> EventStream:
    return EventStream([Event(t=t, node=n, state=s) for t, n, s in pairs])


# ---------------------------------------------------------------------------
# PlayWidget instantiation
# ---------------------------------------------------------------------------


def test_play_widget_instantiation() -> None:
    w = PlayWidget()
    assert isinstance(w, PlayWidget)


def test_play_widget_defaults() -> None:
    w = PlayWidget()
    assert w.width == 800
    assert w.height == 600
    assert w.show_labels is True
    assert w.playback_state == "idle"
    assert w.playback_speed == 1.0
    assert w.current_t == 0.0
    assert w.duration == 0.0
    assert w.events_data == []
    assert w.graph_data == {}


# ---------------------------------------------------------------------------
# biopulse.play()
# ---------------------------------------------------------------------------


def test_play_returns_play_widget() -> None:
    g = _make_graph("A", "B")
    es = _make_events((0.0, "A", 1), (1.0, "B", 1))
    widget = biopulse.play(g, es)
    assert isinstance(widget, PlayWidget)


def test_play_autoplay_default() -> None:
    g = _make_graph("A")
    es = _make_events((1.0, "A", 1))
    widget = biopulse.play(g, es)
    assert widget.playback_state == "playing"


def test_play_autoplay_false() -> None:
    g = _make_graph("A")
    es = _make_events((1.0, "A", 1))
    widget = biopulse.play(g, es, autoplay=False)
    assert widget.playback_state == "idle"


def test_play_speed_forwarded() -> None:
    g = _make_graph("A")
    es = _make_events((1.0, "A", 1))
    widget = biopulse.play(g, es, speed=2.5)
    assert widget.playback_speed == 2.5


def test_play_events_serialised() -> None:
    g = _make_graph("IL6", "STAT3")
    es = _make_events((0.0, "IL6", 1), (1.0, "STAT3", 1))
    widget = biopulse.play(g, es)
    assert len(widget.events_data) == 2
    assert widget.events_data[0] == {"t": 0.0, "node": "IL6", "state": 1}
    assert widget.events_data[1] == {"t": 1.0, "node": "STAT3", "state": 1}


def test_play_events_sorted_in_widget() -> None:
    g = _make_graph("A", "B")
    es = EventStream([Event(t=2.0, node="B", state=1), Event(t=0.5, node="A", state=1)])
    widget = biopulse.play(g, es)
    times = [ev["t"] for ev in widget.events_data]
    assert times == sorted(times)


def test_play_duration_set() -> None:
    g = _make_graph("A", "B")
    es = _make_events((0.0, "A", 1), (3.5, "B", 1))
    widget = biopulse.play(g, es)
    assert widget.duration == 3.5


def test_play_graph_data_has_nodes() -> None:
    g = _make_graph("X", "Y", "Z")
    es = _make_events((0.0, "X", 1))
    widget = biopulse.play(g, es)
    assert set(widget.graph_data["nodes"]) == {"X", "Y", "Z"}


def test_play_dimensions_forwarded() -> None:
    g = _make_graph("A")
    es = _make_events((0.0, "A", 1))
    widget = biopulse.play(g, es, width=1024, height=768)
    assert widget.width == 1024
    assert widget.height == 768


def test_play_empty_events() -> None:
    g = _make_graph("A", "B")
    widget = biopulse.play(g, EventStream())
    assert widget.events_data == []
    assert widget.duration == 0.0


def test_play_with_example_scene() -> None:
    from pathlib import Path

    scene_path = Path(__file__).parent.parent / "examples" / "data" / "il6_stat3.scene.json"
    graph, events = load_scene(scene_path)
    widget = biopulse.play(graph, events, speed=2.0, autoplay=False)
    assert widget.playback_state == "idle"
    assert len(widget.events_data) == 5
    assert widget.duration == 2.0
