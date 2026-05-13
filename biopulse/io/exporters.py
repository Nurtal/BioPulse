"""BioPulse export utilities — JSON round-trip, standalone HTML, GIF and MP4.

Public functions:
    export_graph    — write a Graph to canonical JSON
    export_events   — write an EventStream to canonical JSON
    export_scene    — write Graph + EventStream as a scene JSON
    export_html     — write a self-contained HTML file (static or animated)
    export_gif      — render an animated GIF  (requires ``biopulse[export]``)
    export_mp4      — render an MP4 video     (requires ``biopulse[export]`` + ffmpeg)
"""

from __future__ import annotations

import json
from pathlib import Path
from string import Template
from typing import Any

from biopulse.core.renderer.widget import _CONTROLS_CSS, build_graph_data
from biopulse.layouts.base import Layout
from biopulse.layouts.forceatlas import ForceAtlasLayout
from biopulse.model.events import EventStream
from biopulse.model.graph import Graph
from biopulse.model.schema import EventStream as EventStreamSchema
from biopulse.model.schema import Scene

_RENDERER_DIR = Path(__file__).parent.parent / "core" / "renderer"


def _load_renderer(filename: str) -> str:
    js = (_RENDERER_DIR / filename).read_text(encoding="utf-8")
    return js.replace("export function render", "function render", 1)


# Read JS at module load time so it's cached and tests can swap the renderer dir.
_STATIC_JS = _load_renderer("_pixi_graph.js")
_PLAY_JS = _load_renderer("_pixi_play.js")

# ── Standalone HTML model shim ─────────────────────────────────────────────────
# Mimics the anywidget model interface so the existing render() functions work
# unchanged in a browser without Jupyter.

_MODEL_SHIM_JS = """\
class _BPModel {
  constructor(data) {
    this._data = Object.assign({}, data);
    this._listeners = {};
    this._pending = new Set();
  }
  get(key)      { return this._data[key]; }
  set(key, val) { this._data[key] = val; this._pending.add(key); }
  save_changes() {
    for (const k of this._pending)
      (this._listeners["change:" + k] || []).forEach(cb => cb());
    this._pending.clear();
  }
  on(event, cb) {
    (this._listeners[event] = this._listeners[event] || []).push(cb);
  }
}
"""

# ── HTML templates ─────────────────────────────────────────────────────────────

_HTML_STATIC = Template(
    """\
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>$title</title>
  <style>
    body { margin: 0; background: #1a1a2e; display: flex;
           flex-direction: column; align-items: center; padding: 16px; }
    #bp-app { position: relative; }
  </style>
</head>
<body>
<div id="bp-app"></div>
<script type="module">
$model_shim

// ── Embedded data ──────────────────────────────────────────────────────────
const _GRAPH_DATA   = $graph_data_json;
const _WIDTH        = $width;
const _HEIGHT       = $height;
const _SHOW_LABELS  = $show_labels_js;

// ── Renderer ───────────────────────────────────────────────────────────────
$renderer_js

// ── Bootstrap ──────────────────────────────────────────────────────────────
const _model = new _BPModel({
  graph_data:       _GRAPH_DATA,
  width:            _WIDTH,
  height:           _HEIGHT,
  show_labels:      _SHOW_LABELS,
  highlighted_nodes: [],
});
render({ model: _model, el: document.getElementById("bp-app") });
</script>
</body>
</html>
"""
)

_HTML_PLAY = Template(
    """\
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>$title</title>
  <style>
    body { margin: 0; background: #1a1a2e; display: flex;
           flex-direction: column; align-items: center; padding: 16px; }
    #bp-app { position: relative; }
    $controls_css
  </style>
</head>
<body>
<div id="bp-app"></div>
<script type="module">
$model_shim

// ── Embedded data ──────────────────────────────────────────────────────────
const _GRAPH_DATA   = $graph_data_json;
const _EVENTS_DATA  = $events_data_json;
const _WIDTH        = $width;
const _HEIGHT       = $height;
const _SHOW_LABELS  = $show_labels_js;
const _DURATION     = $duration;
const _SPEED        = $speed;
const _AUTOPLAY     = $autoplay_js;

// ── Renderer ───────────────────────────────────────────────────────────────
$renderer_js

// ── Bootstrap ──────────────────────────────────────────────────────────────
const _model = new _BPModel({
  graph_data:       _GRAPH_DATA,
  events_data:      _EVENTS_DATA,
  width:            _WIDTH,
  height:           _HEIGHT,
  show_labels:      _SHOW_LABELS,
  highlighted_nodes: [],
  playback_state:   _AUTOPLAY ? "playing" : "idle",
  playback_speed:   _SPEED,
  current_t:        0.0,
  duration:         _DURATION,
});
render({ model: _model, el: document.getElementById("bp-app") });
</script>
</body>
</html>
"""
)

# ── JSON round-trip exporters ──────────────────────────────────────────────────


def export_graph(graph: Graph, path: str | Path) -> None:
    """Serialise *graph* to canonical JSON (``{"nodes": [...], "edges": [...]}``).

    The output is round-trippable via :func:`~biopulse.io.json_loader.load_graph`.
    """
    payload = graph.schema.model_dump(exclude_none=True)
    Path(path).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def export_events(events: EventStream, path: str | Path) -> None:
    """Serialise *events* to canonical JSON (``{"events": [...]}``).

    The output is round-trippable via :func:`~biopulse.io.json_loader.load_events`.
    """
    envelope = EventStreamSchema(events=list(events))
    payload = envelope.model_dump()
    Path(path).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def export_scene(graph: Graph, events: EventStream, path: str | Path) -> None:
    """Serialise *graph* + *events* to canonical scene JSON.

    The output is round-trippable via :func:`~biopulse.io.json_loader.load_scene`.
    """
    scene = Scene(graph=graph.schema, events=list(events))
    payload = scene.model_dump(exclude_none=True)
    Path(path).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


# ── HTML export ────────────────────────────────────────────────────────────────


def export_html(
    graph: Graph,
    path: str | Path,
    *,
    events: EventStream | None = None,
    layout: Layout | None = None,
    width: int = 800,
    height: int = 600,
    show_labels: bool = True,
    speed: float = 1.0,
    autoplay: bool = True,
    title: str = "BioPulse",
) -> None:
    """Write a self-contained HTML file that renders *graph* in a browser.

    No Jupyter, Python, or local server is required to open the output.  PixiJS
    is loaded from ``https://esm.sh/pixi.js@7`` (requires an internet connection
    the first time the file is opened).

    When *events* is ``None`` a static interactive graph is exported (zoom/pan,
    hover tooltip, click-to-highlight).  When *events* is provided the full
    animated player is exported including the HTML control bar.

    Args:
        graph: The biological graph to display.
        path: Output file path (written as UTF-8).
        events: Optional animation event stream. Omit for a static export.
        layout: Layout algorithm. Defaults to
            :class:`~biopulse.layouts.forceatlas.ForceAtlasLayout`.
        width: Canvas width in pixels.
        height: Canvas height in pixels.
        show_labels: Whether to render node-id labels.
        speed: Initial playback speed (animated export only).
        autoplay: Start playing immediately (animated export only).
        title: ``<title>`` element content.
    """
    if layout is None:
        layout = ForceAtlasLayout()
    positions = layout.compute(graph)
    graph_data = build_graph_data(graph, positions, width, height)
    graph_data_json = json.dumps(graph_data, ensure_ascii=False)

    if events is None:
        html = _HTML_STATIC.safe_substitute(
            title=title,
            model_shim=_MODEL_SHIM_JS,
            graph_data_json=graph_data_json,
            width=width,
            height=height,
            show_labels_js="true" if show_labels else "false",
            renderer_js=_STATIC_JS,
        )
    else:
        events_list: list[dict[str, Any]] = [
            {"t": e.t, "node": e.node, "state": e.state} for e in events
        ]
        html = _HTML_PLAY.safe_substitute(
            title=title,
            controls_css=_CONTROLS_CSS,
            model_shim=_MODEL_SHIM_JS,
            graph_data_json=graph_data_json,
            events_data_json=json.dumps(events_list, ensure_ascii=False),
            width=width,
            height=height,
            show_labels_js="true" if show_labels else "false",
            duration=events.duration,
            speed=speed,
            autoplay_js="true" if autoplay else "false",
            renderer_js=_PLAY_JS,
        )

    Path(path).write_text(html, encoding="utf-8")


# ── Shared frame-generation logic ──────────────────────────────────────────────


def _build_frames(
    graph: Graph,
    events: EventStream,
    *,
    layout: Layout | None = None,
    width: int = 800,
    height: int = 600,
    fps: int = 24,
    speed: float = 1.0,
    show_labels: bool = True,
) -> list[Any]:
    """Render every animation frame and return a list of PIL Images."""
    import numpy as np

    from biopulse.core.renderer._raster import render_frame  # lazy — requires Pillow

    if layout is None:
        layout = ForceAtlasLayout()
    positions = layout.compute(graph)
    graph_data = build_graph_data(graph, positions, width, height)

    duration = events.duration
    total_time = duration + 0.5  # a brief pause at the end
    n_frames = max(1, int(total_time * fps / speed))
    time_steps = np.linspace(0.0, total_time, n_frames)

    # Build per-frame node_states using a simple replay loop
    events_list = sorted(events, key=lambda e: e.t)
    node_states: dict[str, dict[str, Any]] = {}

    # Cumulative event cursor for efficient sequential rendering
    cursor = 0

    frames = []
    prev_t = 0.0
    for t in time_steps:
        # Dispatch events that fall in (prev_t, t]
        while cursor < len(events_list) and events_list[cursor].t <= t:
            ev = events_list[cursor]
            if ev.t > prev_t:
                prev = node_states.get(ev.node)
                node_states[ev.node] = {
                    "cur": ev.state,
                    "prev": prev["cur"] if prev else 0,
                    "tChanged": ev.t,
                }
            cursor += 1
        frames.append(
            render_frame(graph_data, node_states, float(t), width, height, show_labels=show_labels)
        )
        prev_t = t

    return frames


# ── GIF export ─────────────────────────────────────────────────────────────────


def export_gif(
    graph: Graph,
    events: EventStream,
    path: str | Path,
    *,
    layout: Layout | None = None,
    width: int = 600,
    height: int = 450,
    fps: int = 24,
    speed: float = 1.0,
    show_labels: bool = True,
    loop: int = 0,
) -> None:
    """Export an animated GIF of the simulation.

    Requires ``pip install 'biopulse[export]'`` (Pillow).

    Args:
        graph: The biological graph to animate.
        events: The event stream driving the animation.
        path: Output ``.gif`` file path.
        layout: Layout algorithm. Defaults to
            :class:`~biopulse.layouts.forceatlas.ForceAtlasLayout`.
        width: Frame width in pixels.
        height: Frame height in pixels.
        fps: Frames per second.
        speed: Playback speed multiplier (higher = faster animation).
        show_labels: Whether to draw node-id labels.
        loop: GIF loop count; ``0`` = loop forever.
    """
    frames = _build_frames(
        graph,
        events,
        layout=layout,
        width=width,
        height=height,
        fps=fps,
        speed=speed,
        show_labels=show_labels,
    )
    frame_duration_ms = max(1, round(1000 / fps))
    rgb_frames = [f.convert("RGB") for f in frames]
    rgb_frames[0].save(
        path,
        save_all=True,
        append_images=rgb_frames[1:],
        loop=loop,
        duration=frame_duration_ms,
        optimize=False,
    )


# ── MP4 export ─────────────────────────────────────────────────────────────────


def export_mp4(
    graph: Graph,
    events: EventStream,
    path: str | Path,
    *,
    layout: Layout | None = None,
    width: int = 800,
    height: int = 600,
    fps: int = 30,
    speed: float = 1.0,
    show_labels: bool = True,
) -> None:
    """Export an MP4 video of the simulation.

    Requires ``pip install 'biopulse[export]'`` (Pillow + imageio + ffmpeg).
    If ffmpeg is not installed, install it via ``pip install imageio[ffmpeg]``
    or your system package manager.

    Args:
        graph: The biological graph to animate.
        events: The event stream driving the animation.
        path: Output ``.mp4`` file path.
        layout: Layout algorithm. Defaults to
            :class:`~biopulse.layouts.forceatlas.ForceAtlasLayout`.
        width: Frame width in pixels (should be even for MP4 compatibility).
        height: Frame height in pixels (should be even for MP4 compatibility).
        fps: Frames per second.
        speed: Playback speed multiplier.
        show_labels: Whether to draw node-id labels.
    """
    try:
        import imageio
    except ImportError as exc:
        raise ImportError(
            "imageio is required for MP4 export. Install it with: pip install 'biopulse[export]'"
        ) from exc

    import numpy as np

    # Ensure even dimensions (MP4/h264 requirement)
    width = width + (width % 2)
    height = height + (height % 2)

    frames = _build_frames(
        graph,
        events,
        layout=layout,
        width=width,
        height=height,
        fps=fps,
        speed=speed,
        show_labels=show_labels,
    )
    writer = imageio.get_writer(str(path), fps=fps, codec="libx264", pixelformat="yuv420p")
    try:
        for frame in frames:
            writer.append_data(np.array(frame.convert("RGB")))
    finally:
        writer.close()
