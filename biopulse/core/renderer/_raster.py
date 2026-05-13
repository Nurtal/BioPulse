"""Pillow-based raster renderer for GIF/MP4 frame generation.

Produces PIL Images that match the PixiJS widget's visual style:
dark navy background, cyan active nodes, blue inactive nodes,
teal activation arrows, coral inhibition bars.

Import guard: Pillow is an optional dependency (``pip install biopulse[export]``).
"""

from __future__ import annotations

import math
from typing import Any

try:
    from PIL import Image, ImageDraw, ImageFont

    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False

# ── Visual constants (mirror _pixi_play.js) ────────────────────────────────────

NODE_RADIUS: int = 12
FADE_DUR: float = 0.35
PULSE_DUR: float = 0.45

_BG_RGB = (26, 26, 46)  # 0x1a1a2e
_INACTIVE_RGB = (45, 89, 134)  # 0x2d5986
_ACTIVE_RGB = (79, 195, 247)  # 0x4fc3f7
_LABEL_RGB = (229, 231, 235)  # 0xe5e7eb
_ACTIVATION_RGB = (126, 200, 227)  # 0x7ec8e3
_INHIBITION_RGB = (255, 107, 107)  # 0xff6b6b


def _require_pillow() -> None:
    if not _PIL_AVAILABLE:
        raise ImportError(
            "Pillow is required for raster export. Install it with: pip install 'biopulse[export]'"
        )


# ── Colour interpolation ───────────────────────────────────────────────────────


def _ease_in_out(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def _lerp_rgb(
    c1: tuple[int, int, int],
    c2: tuple[int, int, int],
    t: float,
) -> tuple[int, int, int]:
    t = max(0.0, min(1.0, t))
    return (
        round(c1[0] + (c2[0] - c1[0]) * t),
        round(c1[1] + (c2[1] - c1[1]) * t),
        round(c1[2] + (c2[2] - c1[2]) * t),
    )


def _node_rgb(
    ns: dict[str, Any],
    t: float,
) -> tuple[int, int, int]:
    elapsed = t - ns["tChanged"]
    cur_rgb = _ACTIVE_RGB if ns["cur"] == 1 else _INACTIVE_RGB
    prev_rgb = _ACTIVE_RGB if ns["prev"] == 1 else _INACTIVE_RGB
    if elapsed >= FADE_DUR:
        return cur_rgb
    return _lerp_rgb(prev_rgb, cur_rgb, _ease_in_out(elapsed / FADE_DUR))


def _node_scale(ns: dict[str, Any], t: float) -> float:
    elapsed = t - ns["tChanged"]
    if ns["cur"] == 1 and 0.0 <= elapsed < PULSE_DUR:
        return 1.0 + 0.25 * math.sin(math.pi * elapsed / PULSE_DUR)
    return 1.0


# ── Edge drawing ───────────────────────────────────────────────────────────────


def _draw_arrow(
    draw: ImageDraw.ImageDraw,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    color: tuple[int, int, int],
    alpha: int = 220,
) -> None:
    dx, dy = x2 - x1, y2 - y1
    length = math.sqrt(dx * dx + dy * dy) or 1.0
    ux, uy = dx / length, dy / length
    # Start and end points offset by NODE_RADIUS
    sx, sy = x1 + ux * NODE_RADIUS, y1 + uy * NODE_RADIUS
    ex, ey = x2 - ux * NODE_RADIUS, y2 - uy * NODE_RADIUS
    rgba = (*color, alpha)
    draw.line([(sx, sy), (ex, ey)], fill=rgba, width=2)
    # Arrowhead triangle
    sz = 9
    tip = (ex, ey)
    left = (ex - ux * sz - uy * sz * 0.5, ey - uy * sz + ux * sz * 0.5)
    right = (ex - ux * sz + uy * sz * 0.5, ey - uy * sz - ux * sz * 0.5)
    draw.polygon([tip, left, right], fill=rgba)


def _draw_bar(
    draw: ImageDraw.ImageDraw,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    color: tuple[int, int, int],
    alpha: int = 220,
) -> None:
    dx, dy = x2 - x1, y2 - y1
    length = math.sqrt(dx * dx + dy * dy) or 1.0
    ux, uy = dx / length, dy / length
    sx, sy = x1 + ux * NODE_RADIUS, y1 + uy * NODE_RADIUS
    bx, by = x2 - ux * NODE_RADIUS, y2 - uy * NODE_RADIUS
    rgba = (*color, alpha)
    draw.line([(sx, sy), (bx, by)], fill=rgba, width=2)
    # Flat inhibition bar (perpendicular)
    draw.line(
        [(bx - uy * 9, by + ux * 9), (bx + uy * 9, by - ux * 9)],
        fill=rgba,
        width=3,
    )


# ── Frame renderer ─────────────────────────────────────────────────────────────


def render_frame(
    graph_data: dict[str, Any],
    node_states: dict[str, dict[str, Any]],
    t: float,
    width: int,
    height: int,
    *,
    show_labels: bool = True,
) -> Image.Image:
    """Render one animation frame as a PIL RGBA Image.

    Args:
        graph_data: ``{nodes: {id: {x, y}}, edges: [{source, target, type}]}``
            as produced by :func:`~biopulse.core.renderer.widget.build_graph_data`.
        node_states: ``{id: {cur, prev, tChanged}}`` — current animation state
            per node (same structure used internally by ``_pixi_play.js``).
        t: Current playback time in seconds.
        width: Frame width in pixels.
        height: Frame height in pixels.
        show_labels: Whether to draw node-id labels.

    Returns:
        A ``PIL.Image.Image`` in RGBA mode.
    """
    _require_pillow()

    img = Image.new("RGBA", (width, height), color=(*_BG_RGB, 255))
    draw = ImageDraw.Draw(img, "RGBA")

    nodes: dict[str, dict[str, Any]] = graph_data.get("nodes", {})
    edges: list[dict[str, Any]] = graph_data.get("edges", [])

    # ── Edges ──────────────────────────────────────────────────────────────────
    for edge in edges:
        src = nodes.get(edge["source"])
        tgt = nodes.get(edge["target"])
        if src is None or tgt is None:
            continue
        if edge["type"] == "inhibition":
            _draw_bar(draw, src["x"], src["y"], tgt["x"], tgt["y"], _INHIBITION_RGB)
        else:
            _draw_arrow(draw, src["x"], src["y"], tgt["x"], tgt["y"], _ACTIVATION_RGB)

    # ── Nodes ──────────────────────────────────────────────────────────────────
    _default_ns: dict[str, Any] = {"cur": 0, "prev": 0, "tChanged": -999.0}
    for node_id, pos in nodes.items():
        ns = node_states.get(node_id, _default_ns)
        rgb = _node_rgb(ns, t)
        scale = _node_scale(ns, t)
        r = NODE_RADIUS * scale
        x, y = pos["x"], pos["y"]
        draw.ellipse([x - r, y - r, x + r, y + r], fill=(*rgb, 255))

    # ── Labels ─────────────────────────────────────────────────────────────────
    if show_labels:
        try:
            font = ImageFont.load_default(size=11)
        except TypeError:
            font = ImageFont.load_default()
        for node_id, pos in nodes.items():
            x, y = pos["x"], pos["y"]
            draw.text((x, y - NODE_RADIUS - 14), node_id, font=font, fill=_LABEL_RGB, anchor="mm")

    return img
