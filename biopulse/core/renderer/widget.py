"""GraphWidget and PlayWidget — anywidget-based PixiJS renderers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import anywidget
import traitlets

from biopulse.model.graph import Graph

_JS = (Path(__file__).parent / "_pixi_graph.js").read_text(encoding="utf-8")
_PLAY_JS = (Path(__file__).parent / "_pixi_play.js").read_text(encoding="utf-8")

_CONTROLS_CSS = """
.bp-controls {
  display: flex; align-items: center; gap: 6px;
  padding: 5px 8px; background: #0d1117;
  border-top: 1px solid #1f2937; user-select: none;
}
.bp-controls button {
  background: #1f2937; color: #cbd5e1;
  border: 1px solid #374151; border-radius: 4px;
  padding: 2px 8px; cursor: pointer; font-size: 12px; line-height: 1.5;
}
.bp-controls button:hover { background: #374151; }
.bp-controls button.bp-active { background: #1d4ed8; border-color: #3b82f6; color: #fff; }
.bp-controls input[type=range] { flex: 1; min-width: 60px; accent-color: #4fc3f7; cursor: pointer; }
.bp-controls .bp-time { color: #9ca3af; font-size: 11px; font-family: monospace; min-width: 40px; }
"""


class GraphWidget(anywidget.AnyWidget):
    """Jupyter widget that renders a static biological graph with PixiJS.

    Supports zoom/pan (scroll + drag), node hover tooltips, and click-to-highlight
    upstream/downstream paths.  Python can also set :attr:`highlighted_nodes`
    to drive highlights programmatically.
    """

    _esm = _JS
    _css = ""

    graph_data: Any = traitlets.Dict({}).tag(sync=True)
    width: Any = traitlets.Int(800).tag(sync=True)
    height: Any = traitlets.Int(600).tag(sync=True)
    show_labels: Any = traitlets.Bool(True).tag(sync=True)
    highlighted_nodes: Any = traitlets.List([]).tag(sync=True)
    glow_enabled: Any = traitlets.Bool(False).tag(sync=True)


class PlayWidget(anywidget.AnyWidget):
    """Jupyter widget that animates a biological graph driven by an EventStream.

    Playback is entirely client-side (PixiJS ticker at 60 fps).  The control bar
    (restart / play-pause / speed / scrubber) is rendered as HTML below the canvas.

    Python controls start/pause/seek via the synced traitlets below.
    """

    _esm = _PLAY_JS
    _css = _CONTROLS_CSS

    graph_data: Any = traitlets.Dict({}).tag(sync=True)
    width: Any = traitlets.Int(800).tag(sync=True)
    height: Any = traitlets.Int(600).tag(sync=True)
    show_labels: Any = traitlets.Bool(True).tag(sync=True)
    highlighted_nodes: Any = traitlets.List([]).tag(sync=True)

    events_data: Any = traitlets.List([]).tag(sync=True)
    playback_state: Any = traitlets.Unicode("idle").tag(sync=True)
    playback_speed: Any = traitlets.Float(1.0).tag(sync=True)
    current_t: Any = traitlets.Float(0.0).tag(sync=True)
    duration: Any = traitlets.Float(0.0).tag(sync=True)
    glow_enabled: Any = traitlets.Bool(True).tag(sync=True)
    pulse_ring_enabled: Any = traitlets.Bool(True).tag(sync=True)
    heatmap_enabled: Any = traitlets.Bool(False).tag(sync=True)
    particles_enabled: Any = traitlets.Bool(False).tag(sync=True)


def _positions_to_pixels(
    positions: dict[str, tuple[float, float]],
    width: int,
    height: int,
    margin: int = 60,
) -> dict[str, dict[str, float]]:
    """Map float layout positions to canvas pixel coordinates."""
    if not positions:
        return {}
    xs = [p[0] for p in positions.values()]
    ys = [p[1] for p in positions.values()]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    x_range = max(x_max - x_min, 1e-9)
    y_range = max(y_max - y_min, 1e-9)
    draw_w = width - 2 * margin
    draw_h = height - 2 * margin
    return {
        nid: {
            "x": margin + (x - x_min) / x_range * draw_w,
            "y": margin + (y - y_min) / y_range * draw_h,
        }
        for nid, (x, y) in positions.items()
    }


def build_graph_data(
    graph: Graph,
    positions: dict[str, tuple[float, float]],
    width: int,
    height: int,
    margin: int = 60,
) -> dict[str, Any]:
    """Serialise *graph* and *positions* into the dict consumed by the JS widgets.

    Each node entry contains ``x``, ``y`` (pixels) and, if present, ``group``
    (used by the hover tooltip).
    """
    pixel_pos = _positions_to_pixels(positions, width, height, margin)
    nodes: dict[str, dict[str, Any]] = {}
    for node in graph.schema.nodes:
        pos = pixel_pos.get(node.id, {"x": 0.0, "y": 0.0})
        entry: dict[str, Any] = {"x": pos["x"], "y": pos["y"]}
        if node.group is not None:
            entry["group"] = node.group
        nodes[node.id] = entry
    edges: list[dict[str, str]] = [
        {"source": e.source, "target": e.target, "type": e.type} for e in graph.schema.edges
    ]
    return {"nodes": nodes, "edges": edges}
