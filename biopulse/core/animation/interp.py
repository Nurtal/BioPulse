"""Interpolation utilities for smooth visual transitions."""

from __future__ import annotations

import math


def ease_in_out(t: float) -> float:
    """Smoothstep (cubic ease-in-out) for *t* in [0, 1].

    Values outside [0, 1] are clamped. Returns 0 at t=0, 1 at t=1,
    with zero velocity at both endpoints.
    """
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between *a* and *b* at parameter *t*."""
    return a + (b - a) * t


def lerp_color(c1: int, c2: int, t: float) -> int:
    """Linearly interpolate between two packed 24-bit RGB colours.

    *c1* and *c2* are integers of the form ``0xRRGGBB``.
    *t* is clamped to [0, 1].
    """
    t = max(0.0, min(1.0, t))
    r1, g1, b1 = (c1 >> 16) & 0xFF, (c1 >> 8) & 0xFF, c1 & 0xFF
    r2, g2, b2 = (c2 >> 16) & 0xFF, (c2 >> 8) & 0xFF, c2 & 0xFF
    r = round(r1 + (r2 - r1) * t)
    g = round(g1 + (g2 - g1) * t)
    b = round(b1 + (b2 - b1) * t)
    return (r << 16) | (g << 8) | b


def ring_progress(elapsed: float, duration: float) -> float:
    """Return the normalised progress [0, 1] of an expanding ring animation.

    Returns 0 at ``elapsed = 0`` (ring at base radius) and 1 at
    ``elapsed >= duration`` (ring fully expanded).  Values outside [0, 1]
    are clamped so callers can use this to gate rendering without checking
    bounds themselves.
    """
    if duration <= 0:
        return 1.0
    return max(0.0, min(1.0, elapsed / duration))


def ring_alpha(elapsed: float, duration: float, peak: float = 0.7) -> float:
    """Alpha for an expanding ring: *peak* at ``elapsed=0``, 0 at ``elapsed=duration``."""
    return peak * (1.0 - ring_progress(elapsed, duration))


def ring_radius(elapsed: float, duration: float, base: float, expansion: float = 2.5) -> float:
    """Radius for an expanding ring that grows from *base* to ``base * (1 + expansion)``."""
    return base * (1.0 + expansion * ring_progress(elapsed, duration))


def heatmap_color(
    count: int,
    max_count: int,
    cold: int = 0x2D5986,
    hot: int = 0xFF9A00,
) -> int:
    """Map a cumulative activation *count* to a packed 24-bit RGB colour.

    Returns *cold* when ``count == 0`` and *hot* when ``count >= max_count``.
    Intermediate values are linearly interpolated.

    Args:
        count: Number of activations for the node.
        max_count: The maximum activation count in the network (used for normalisation).
        cold: Packed RGB colour for zero activations (default: BioPulse inactive blue).
        hot: Packed RGB colour for maximum activations (default: amber ``0xFF9A00``).
    """
    if max_count <= 0 or count <= 0:
        return cold
    return lerp_color(cold, hot, min(count / max_count, 1.0))


def pulse_scale(elapsed: float, duration: float, amplitude: float = 0.25) -> float:
    """Scale factor for a single sinusoidal pulse over *duration* seconds.

    * At ``elapsed = 0``: scale = 1.0 (starts at rest).
    * At ``elapsed = duration / 2``: scale = 1 + *amplitude* (peak).
    * At ``elapsed >= duration``: scale = 1.0 (returns to rest).
    """
    if duration <= 0 or elapsed >= duration:
        return 1.0
    return 1.0 + amplitude * math.sin(math.pi * elapsed / duration)
