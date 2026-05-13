"""Tests for Phase 6 exporters: JSON round-trip and standalone HTML."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import biopulse
from biopulse.io.exporters import export_events, export_graph, export_html, export_scene
from biopulse.io.json_loader import load_events, load_graph, load_scene
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


# ===========================================================================
# export_graph — JSON round-trip
# ===========================================================================


class TestExportGraph:
    def test_creates_file(self, tmp_path: Path) -> None:
        g = _make_graph("A", "B")
        p = tmp_path / "graph.json"
        export_graph(g, p)
        assert p.exists()

    def test_public_api_alias(self) -> None:
        assert biopulse.export_graph is export_graph

    def test_round_trip_nodes(self, tmp_path: Path) -> None:
        g = _make_graph("IL6", "STAT3")
        p = tmp_path / "graph.json"
        export_graph(g, p)
        g2 = load_graph(p)
        assert {n.id for n in g2.schema.nodes} == {"IL6", "STAT3"}

    def test_round_trip_edges(self, tmp_path: Path) -> None:
        g = _make_graph("A", "B", edges=[("A", "B", "inhibition")])
        p = tmp_path / "graph.json"
        export_graph(g, p)
        g2 = load_graph(p)
        assert len(g2.schema.edges) == 1
        assert g2.schema.edges[0].type == "inhibition"

    def test_group_preserved(self, tmp_path: Path) -> None:
        g = _make_graph("A", groups={"A": "kinase"})
        p = tmp_path / "graph.json"
        export_graph(g, p)
        g2 = load_graph(p)
        assert g2.schema.nodes[0].group == "kinase"

    def test_no_group_omitted_from_json(self, tmp_path: Path) -> None:
        g = _make_graph("A")
        p = tmp_path / "graph.json"
        export_graph(g, p)
        raw = json.loads(p.read_text())
        assert "group" not in raw["nodes"][0]

    def test_valid_json(self, tmp_path: Path) -> None:
        g = _make_graph("X", "Y", "Z", edges=[("X", "Y", "activation")])
        p = tmp_path / "graph.json"
        export_graph(g, p)
        data = json.loads(p.read_text())
        assert "nodes" in data and "edges" in data

    def test_accepts_string_path(self, tmp_path: Path) -> None:
        g = _make_graph("A")
        export_graph(g, str(tmp_path / "g.json"))

    def test_empty_graph(self, tmp_path: Path) -> None:
        g = Graph(GraphSchema.model_validate({"nodes": []}))
        p = tmp_path / "empty.json"
        export_graph(g, p)
        g2 = load_graph(p)
        assert g2.schema.nodes == []


# ===========================================================================
# export_events — JSON round-trip
# ===========================================================================


class TestExportEvents:
    def test_creates_file(self, tmp_path: Path) -> None:
        es = _make_events((0.0, "A", 1))
        export_events(es, tmp_path / "ev.json")
        assert (tmp_path / "ev.json").exists()

    def test_public_api_alias(self) -> None:
        assert biopulse.export_events is export_events

    def test_round_trip(self, tmp_path: Path) -> None:
        es = _make_events((0.0, "A", 1), (1.5, "B", 0))
        p = tmp_path / "ev.json"
        export_events(es, p)
        es2 = load_events(p)
        assert len(es2) == 2
        assert es2._events[0].t == pytest.approx(0.0)
        assert es2._events[1].t == pytest.approx(1.5)

    def test_events_sorted_in_output(self, tmp_path: Path) -> None:
        es = EventStream([Event(t=2.0, node="B", state=1), Event(t=0.5, node="A", state=1)])
        p = tmp_path / "ev.json"
        export_events(es, p)
        es2 = load_events(p)
        times = [e.t for e in es2]
        assert times == sorted(times)

    def test_empty_events(self, tmp_path: Path) -> None:
        p = tmp_path / "empty.json"
        export_events(EventStream(), p)
        data = json.loads(p.read_text())
        assert data == {"events": []}

    def test_envelope_structure(self, tmp_path: Path) -> None:
        p = tmp_path / "ev.json"
        export_events(_make_events((1.0, "X", 1)), p)
        data = json.loads(p.read_text())
        assert "events" in data
        assert data["events"][0] == {"t": 1.0, "node": "X", "state": 1}


# ===========================================================================
# export_scene — JSON round-trip
# ===========================================================================


class TestExportScene:
    def test_creates_file(self, tmp_path: Path) -> None:
        g = _make_graph("A", "B")
        es = _make_events((0.0, "A", 1))
        export_scene(g, es, tmp_path / "scene.json")
        assert (tmp_path / "scene.json").exists()

    def test_public_api_alias(self) -> None:
        assert biopulse.export_scene is export_scene

    def test_round_trip(self, tmp_path: Path) -> None:
        g = _make_graph("IL6", "STAT3", edges=[("IL6", "STAT3", "activation")])
        es = _make_events((0.0, "IL6", 1), (1.0, "STAT3", 1))
        p = tmp_path / "scene.json"
        export_scene(g, es, p)
        g2, es2 = load_scene(p)
        assert {n.id for n in g2.schema.nodes} == {"IL6", "STAT3"}
        assert len(es2) == 2

    def test_json_has_graph_and_events_keys(self, tmp_path: Path) -> None:
        p = tmp_path / "scene.json"
        export_scene(_make_graph("A"), _make_events((0.0, "A", 1)), p)
        data = json.loads(p.read_text())
        assert "graph" in data and "events" in data

    def test_cross_validation_still_applies(self, tmp_path: Path) -> None:
        g = _make_graph("A")
        es = EventStream([Event(t=0.0, node="UNKNOWN", state=1)])
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            export_scene(g, es, tmp_path / "bad.json")


# ===========================================================================
# export_html — static
# ===========================================================================


class TestExportHtmlStatic:
    def test_creates_file(self, tmp_path: Path) -> None:
        g = _make_graph("A", "B")
        export_html(g, tmp_path / "graph.html")
        assert (tmp_path / "graph.html").exists()

    def test_public_api_alias(self) -> None:
        assert biopulse.export_html is export_html

    def test_is_valid_html(self, tmp_path: Path) -> None:
        g = _make_graph("A", "B")
        p = tmp_path / "graph.html"
        export_html(g, p)
        content = p.read_text()
        assert content.startswith("<!DOCTYPE html>")
        assert "</html>" in content

    def test_contains_node_ids(self, tmp_path: Path) -> None:
        g = _make_graph("IL6", "STAT3")
        p = tmp_path / "graph.html"
        export_html(g, p)
        content = p.read_text()
        assert "IL6" in content
        assert "STAT3" in content

    def test_custom_title(self, tmp_path: Path) -> None:
        g = _make_graph("A")
        p = tmp_path / "graph.html"
        export_html(g, p, title="My Network")
        assert "My Network" in p.read_text()

    def test_dimensions_embedded(self, tmp_path: Path) -> None:
        g = _make_graph("A")
        p = tmp_path / "graph.html"
        export_html(g, p, width=1024, height=768)
        content = p.read_text()
        assert "1024" in content
        assert "768" in content

    def test_show_labels_false_embedded(self, tmp_path: Path) -> None:
        g = _make_graph("A")
        p = tmp_path / "graph.html"
        export_html(g, p, show_labels=False)
        assert "false" in p.read_text()

    def test_contains_pixi_cdn(self, tmp_path: Path) -> None:
        g = _make_graph("A")
        p = tmp_path / "graph.html"
        export_html(g, p)
        assert "esm.sh/pixi.js" in p.read_text()

    def test_no_events_key_in_static(self, tmp_path: Path) -> None:
        g = _make_graph("A")
        p = tmp_path / "graph.html"
        export_html(g, p)
        assert "events_data" not in p.read_text()

    def test_accepts_string_path(self, tmp_path: Path) -> None:
        g = _make_graph("A")
        export_html(g, str(tmp_path / "g.html"))


# ===========================================================================
# export_html — animated
# ===========================================================================


class TestExportHtmlAnimated:
    def test_creates_file(self, tmp_path: Path) -> None:
        g = _make_graph("A", "B")
        es = _make_events((0.0, "A", 1))
        export_html(g, tmp_path / "play.html", events=es)
        assert (tmp_path / "play.html").exists()

    def test_contains_events_data(self, tmp_path: Path) -> None:
        g = _make_graph("A", "B")
        es = _make_events((0.0, "A", 1), (1.0, "B", 1))
        p = tmp_path / "play.html"
        export_html(g, p, events=es)
        content = p.read_text()
        assert "events_data" in content
        assert '"node": "A"' in content or '"node":"A"' in content

    def test_contains_controls_css(self, tmp_path: Path) -> None:
        g = _make_graph("A")
        es = _make_events((0.0, "A", 1))
        p = tmp_path / "play.html"
        export_html(g, p, events=es)
        assert "bp-controls" in p.read_text()

    def test_duration_embedded(self, tmp_path: Path) -> None:
        g = _make_graph("A")
        es = _make_events((0.0, "A", 1), (3.5, "A", 0))
        p = tmp_path / "play.html"
        export_html(g, p, events=es)
        assert "3.5" in p.read_text()

    def test_speed_embedded(self, tmp_path: Path) -> None:
        g = _make_graph("A")
        es = _make_events((0.0, "A", 1))
        p = tmp_path / "play.html"
        export_html(g, p, events=es, speed=2.0)
        assert "2.0" in p.read_text()

    def test_autoplay_false(self, tmp_path: Path) -> None:
        g = _make_graph("A")
        es = _make_events((0.0, "A", 1))
        p = tmp_path / "play.html"
        export_html(g, p, events=es, autoplay=False)
        assert "false" in p.read_text()
