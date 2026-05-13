"""BioPulse — dynamic visualization engine for Boolean and biological networks."""

from __future__ import annotations

from biopulse.core.renderer.widget import GraphWidget, PlayWidget, build_graph_data
from biopulse.io.exporters import (
    export_events,
    export_gif,
    export_graph,
    export_html,
    export_mp4,
    export_scene,
)
from biopulse.layouts.base import Layout
from biopulse.layouts.forceatlas import ForceAtlasLayout
from biopulse.model.events import EventStream
from biopulse.model.graph import Graph
from biopulse.parsers.ginml import parse_ginml
from biopulse.parsers.sbml import parse_sbml
from biopulse.parsers.sif import parse_sif

__version__ = "0.0.0"
__all__ = [
    "ForceAtlasLayout",
    "Graph",
    "GraphWidget",
    "Layout",
    "PlayWidget",
    "export_events",
    "export_gif",
    "export_graph",
    "export_html",
    "export_mp4",
    "export_scene",
    "parse_ginml",
    "parse_sbml",
    "parse_sif",
    "play",
    "show",
]


def show(
    graph: Graph,
    *,
    layout: Layout | None = None,
    width: int = 800,
    height: int = 600,
    show_labels: bool = True,
) -> GraphWidget:
    """Render *graph* as a static interactive widget in a Jupyter notebook.

    Args:
        graph: The biological graph to display.
        layout: Layout algorithm. Defaults to :class:`ForceAtlasLayout`.
        width: Canvas width in pixels.
        height: Canvas height in pixels.
        show_labels: Whether to render node-id labels.

    Returns:
        A :class:`GraphWidget` that displays automatically when returned from
        a Jupyter cell, or via ``IPython.display.display(widget)``.
    """
    if layout is None:
        layout = ForceAtlasLayout()
    positions = layout.compute(graph)
    data = build_graph_data(graph, positions, width, height)
    return GraphWidget(
        graph_data=data,
        width=width,
        height=height,
        show_labels=show_labels,
    )


def play(
    graph: Graph,
    events: EventStream,
    *,
    layout: Layout | None = None,
    width: int = 800,
    height: int = 600,
    show_labels: bool = True,
    speed: float = 1.0,
    autoplay: bool = True,
) -> PlayWidget:
    """Animate *graph* driven by *events* in a Jupyter notebook.

    Playback runs entirely client-side at 60 fps via PixiJS. Node activations
    trigger a colour fade (inactive → cyan) and a brief scale pulse.

    Args:
        graph: The biological graph to display.
        events: Time-sorted event stream from :func:`~biopulse.io.json_loader.load_scene`
            or :class:`~biopulse.model.events.EventStream`.
        layout: Layout algorithm. Defaults to :class:`ForceAtlasLayout`.
        width: Canvas width in pixels.
        height: Canvas height in pixels.
        show_labels: Whether to render node-id labels.
        speed: Playback speed multiplier (1.0 = real-time, 2.0 = double speed).
        autoplay: Start playing immediately. Set ``False`` to start paused.

    Returns:
        A :class:`PlayWidget` that displays automatically when returned from
        a Jupyter cell, or via ``IPython.display.display(widget)``.
    """
    if layout is None:
        layout = ForceAtlasLayout()
    positions = layout.compute(graph)
    data = build_graph_data(graph, positions, width, height)
    events_list = [{"t": e.t, "node": e.node, "state": e.state} for e in events]
    return PlayWidget(
        graph_data=data,
        width=width,
        height=height,
        show_labels=show_labels,
        events_data=events_list,
        playback_state="playing" if autoplay else "idle",
        playback_speed=speed,
        duration=events.duration,
    )
