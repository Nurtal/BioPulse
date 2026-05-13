"""Tests for biopulse.core.renderer.widget and the show() public API.

Visual / browser rendering is not tested here — those require a Jupyter
environment. These tests cover the Python-side data transformation layer only.
"""

from __future__ import annotations

import math

import pytest

import biopulse
from biopulse.core.renderer.widget import GraphWidget, _positions_to_pixels, build_graph_data
from biopulse.model.graph import Graph
from biopulse.model.schema import Graph as GraphSchema


def _make_graph(*node_ids: str, edges: list[tuple[str, str, str]] | None = None) -> Graph:
    nodes = [{"id": nid} for nid in node_ids]
    edge_dicts = [{"source": s, "target": t, "type": et} for s, t, et in edges] if edges else []
    return Graph(GraphSchema.model_validate({"nodes": nodes, "edges": edge_dicts}))


# ---------------------------------------------------------------------------
# _positions_to_pixels
# ---------------------------------------------------------------------------


def test_pixels_all_nodes_present() -> None:
    pos = {"A": (0.0, 0.0), "B": (1.0, 1.0)}
    px = _positions_to_pixels(pos, 800, 600)
    assert set(px) == {"A", "B"}


def test_pixels_within_canvas() -> None:
    pos = {"A": (-1.0, -1.0), "B": (0.0, 0.5), "C": (1.0, 1.0)}
    margin = 60
    px = _positions_to_pixels(pos, 800, 600, margin=margin)
    for node_px in px.values():
        assert margin <= node_px["x"] <= 800 - margin
        assert margin <= node_px["y"] <= 600 - margin


def test_pixels_extreme_nodes_at_margin() -> None:
    pos = {"min": (-1.0, -1.0), "max": (1.0, 1.0)}
    margin = 50
    px = _positions_to_pixels(pos, 400, 300, margin=margin)
    assert px["min"]["x"] == pytest.approx(margin)
    assert px["min"]["y"] == pytest.approx(margin)
    assert px["max"]["x"] == pytest.approx(400 - margin)
    assert px["max"]["y"] == pytest.approx(300 - margin)


def test_pixels_empty_positions() -> None:
    assert _positions_to_pixels({}, 800, 600) == {}


def test_pixels_single_node_centered() -> None:
    pos = {"X": (0.5, 0.5)}
    margin = 60
    px = _positions_to_pixels(pos, 800, 600, margin=margin)
    # Single node: degenerate range → x_range hits 1e-9, so x = margin + 0
    assert math.isfinite(px["X"]["x"])
    assert math.isfinite(px["X"]["y"])


def test_pixels_values_are_floats() -> None:
    pos = {"A": (0.0, 0.0), "B": (1.0, 1.0)}
    px = _positions_to_pixels(pos, 800, 600)
    for v in px.values():
        assert isinstance(v["x"], float)
        assert isinstance(v["y"], float)


# ---------------------------------------------------------------------------
# build_graph_data
# ---------------------------------------------------------------------------


def test_build_graph_data_structure() -> None:
    g = _make_graph("IL6", "STAT3", edges=[("IL6", "STAT3", "activation")])
    pos = {"IL6": (0.0, 0.0), "STAT3": (1.0, 1.0)}
    data = build_graph_data(g, pos, 800, 600)
    assert "nodes" in data
    assert "edges" in data


def test_build_graph_data_nodes_have_xy() -> None:
    g = _make_graph("A", "B")
    pos = {"A": (0.0, 0.5), "B": (1.0, 0.5)}
    data = build_graph_data(g, pos, 800, 600)
    for node_px in data["nodes"].values():
        assert "x" in node_px and "y" in node_px


def test_build_graph_data_edges() -> None:
    g = _make_graph("A", "B", edges=[("A", "B", "inhibition")])
    pos = {"A": (0.0, 0.0), "B": (1.0, 1.0)}
    data = build_graph_data(g, pos, 800, 600)
    assert len(data["edges"]) == 1
    edge = data["edges"][0]
    assert edge["source"] == "A"
    assert edge["target"] == "B"
    assert edge["type"] == "inhibition"


# ---------------------------------------------------------------------------
# GraphWidget instantiation
# ---------------------------------------------------------------------------


def test_widget_can_be_instantiated() -> None:
    w = GraphWidget()
    assert isinstance(w, GraphWidget)


def test_widget_default_traitlets() -> None:
    w = GraphWidget()
    assert w.width == 800
    assert w.height == 600
    assert w.show_labels is True
    assert w.graph_data == {}


def test_widget_accepts_graph_data() -> None:
    data = {"nodes": {"X": {"x": 100.0, "y": 200.0}}, "edges": []}
    w = GraphWidget(graph_data=data, width=400, height=300)
    assert w.width == 400
    assert w.graph_data["nodes"]["X"]["x"] == 100.0


# ---------------------------------------------------------------------------
# show() public API
# ---------------------------------------------------------------------------


def test_show_returns_graph_widget() -> None:
    g = _make_graph("A", "B", edges=[("A", "B", "activation")])
    widget = biopulse.show(g)
    assert isinstance(widget, GraphWidget)


def test_show_graph_data_has_all_nodes() -> None:
    g = _make_graph("X", "Y", "Z")
    widget = biopulse.show(g)
    assert set(widget.graph_data["nodes"]) == {"X", "Y", "Z"}


def test_show_respects_dimensions() -> None:
    g = _make_graph("A", "B")
    widget = biopulse.show(g, width=400, height=300)
    assert widget.width == 400
    assert widget.height == 300


def test_show_labels_flag_forwarded() -> None:
    g = _make_graph("A")
    assert biopulse.show(g, show_labels=False).show_labels is False
    assert biopulse.show(g, show_labels=True).show_labels is True


def test_show_custom_layout() -> None:
    from biopulse.layouts.forceatlas import ForceAtlasLayout

    g = _make_graph("A", "B", "C")
    layout = ForceAtlasLayout(seed=123, iterations=10)
    widget = biopulse.show(g, layout=layout)
    assert set(widget.graph_data["nodes"]) == {"A", "B", "C"}


def test_show_empty_graph() -> None:
    g = Graph(GraphSchema.model_validate({"nodes": []}))
    widget = biopulse.show(g)
    assert widget.graph_data["nodes"] == {}
    assert widget.graph_data["edges"] == []
