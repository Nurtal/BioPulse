"""Phase 4 tests: highlighted_nodes, group field in graph_data, CSS controls."""

from __future__ import annotations

import biopulse
from biopulse.core.renderer.widget import (
    _CONTROLS_CSS,
    GraphWidget,
    PlayWidget,
    build_graph_data,
)
from biopulse.model.events import EventStream
from biopulse.model.graph import Graph
from biopulse.model.schema import Event
from biopulse.model.schema import Graph as GraphSchema


def _make_graph(
    *node_ids: str,
    edges: list[tuple[str, str, str]] | None = None,
    groups: dict[str, str] | None = None,
) -> Graph:
    nodes = [
        {"id": nid, **({"group": groups[nid]} if groups and nid in groups else {})}
        for nid in node_ids
    ]
    edge_dicts = [{"source": s, "target": t, "type": et} for s, t, et in edges] if edges else []
    return Graph(GraphSchema.model_validate({"nodes": nodes, "edges": edge_dicts}))


def _make_events(*pairs: tuple[float, str, int]) -> EventStream:
    return EventStream([Event(t=t, node=n, state=s) for t, n, s in pairs])


# ---------------------------------------------------------------------------
# highlighted_nodes traitlet — GraphWidget
# ---------------------------------------------------------------------------


def test_graph_widget_highlighted_nodes_default() -> None:
    w = GraphWidget()
    assert w.highlighted_nodes == []


def test_graph_widget_highlighted_nodes_set() -> None:
    w = GraphWidget()
    w.highlighted_nodes = ["A", "B"]
    assert w.highlighted_nodes == ["A", "B"]


def test_graph_widget_highlighted_nodes_constructor() -> None:
    w = GraphWidget(highlighted_nodes=["X"])
    assert w.highlighted_nodes == ["X"]


# ---------------------------------------------------------------------------
# highlighted_nodes traitlet — PlayWidget
# ---------------------------------------------------------------------------


def test_play_widget_highlighted_nodes_default() -> None:
    w = PlayWidget()
    assert w.highlighted_nodes == []


def test_play_widget_highlighted_nodes_set() -> None:
    w = PlayWidget()
    w.highlighted_nodes = ["STAT3"]
    assert w.highlighted_nodes == ["STAT3"]


def test_play_widget_highlighted_nodes_via_play_api() -> None:
    g = _make_graph("A", "B")
    es = _make_events((0.0, "A", 1))
    widget = biopulse.play(g, es)
    assert widget.highlighted_nodes == []


# ---------------------------------------------------------------------------
# group field in build_graph_data
# ---------------------------------------------------------------------------


def test_build_graph_data_group_included() -> None:
    g = _make_graph("IL6", "STAT3", groups={"IL6": "cytokine", "STAT3": "transcription_factor"})
    pos = {"IL6": (0.0, 0.0), "STAT3": (1.0, 1.0)}
    data = build_graph_data(g, pos, 800, 600)
    assert data["nodes"]["IL6"]["group"] == "cytokine"
    assert data["nodes"]["STAT3"]["group"] == "transcription_factor"


def test_build_graph_data_no_group_when_absent() -> None:
    g = _make_graph("A", "B")
    pos = {"A": (0.0, 0.0), "B": (1.0, 1.0)}
    data = build_graph_data(g, pos, 800, 600)
    assert "group" not in data["nodes"]["A"]
    assert "group" not in data["nodes"]["B"]


def test_build_graph_data_mixed_groups() -> None:
    g = _make_graph("A", "B", groups={"A": "kinase"})
    pos = {"A": (0.0, 0.0), "B": (1.0, 1.0)}
    data = build_graph_data(g, pos, 800, 600)
    assert data["nodes"]["A"]["group"] == "kinase"
    assert "group" not in data["nodes"]["B"]


def test_show_graph_data_includes_group() -> None:
    g = _make_graph("X", "Y", groups={"X": "receptor"})
    widget = biopulse.show(g)
    assert widget.graph_data["nodes"]["X"]["group"] == "receptor"
    assert "group" not in widget.graph_data["nodes"]["Y"]


def test_play_graph_data_includes_group() -> None:
    g = _make_graph("IL6", "JAK1", groups={"IL6": "cytokine", "JAK1": "kinase"})
    es = _make_events((0.0, "IL6", 1))
    widget = biopulse.play(g, es)
    assert widget.graph_data["nodes"]["IL6"]["group"] == "cytokine"
    assert widget.graph_data["nodes"]["JAK1"]["group"] == "kinase"


# ---------------------------------------------------------------------------
# CSS controls
# ---------------------------------------------------------------------------


def test_controls_css_non_empty() -> None:
    assert len(_CONTROLS_CSS) > 0


def test_controls_css_has_bp_controls_class() -> None:
    assert ".bp-controls" in _CONTROLS_CSS


def test_controls_css_has_bp_active_class() -> None:
    assert ".bp-active" in _CONTROLS_CSS


def test_play_widget_has_css() -> None:
    w = PlayWidget()
    assert w._css  # non-empty


def test_graph_widget_has_no_css() -> None:
    w = GraphWidget()
    assert w._css == ""
