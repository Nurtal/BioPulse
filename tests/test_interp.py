"""Tests for biopulse.core.animation.interp."""

from __future__ import annotations

import math

import pytest

from biopulse.core.animation.interp import ease_in_out, lerp, lerp_color, pulse_scale

# ---------------------------------------------------------------------------
# ease_in_out
# ---------------------------------------------------------------------------


def test_ease_in_out_endpoints() -> None:
    assert ease_in_out(0.0) == pytest.approx(0.0)
    assert ease_in_out(1.0) == pytest.approx(1.0)


def test_ease_in_out_midpoint() -> None:
    assert ease_in_out(0.5) == pytest.approx(0.5)


def test_ease_in_out_symmetric() -> None:
    for t in [0.1, 0.2, 0.3, 0.4]:
        assert ease_in_out(t) == pytest.approx(1.0 - ease_in_out(1.0 - t))


def test_ease_in_out_clamps_below_zero() -> None:
    assert ease_in_out(-1.0) == pytest.approx(0.0)


def test_ease_in_out_clamps_above_one() -> None:
    assert ease_in_out(2.0) == pytest.approx(1.0)


def test_ease_in_out_monotone() -> None:
    values = [ease_in_out(t / 10) for t in range(11)]
    assert all(values[i] <= values[i + 1] for i in range(len(values) - 1))


# ---------------------------------------------------------------------------
# lerp
# ---------------------------------------------------------------------------


def test_lerp_start() -> None:
    assert lerp(0.0, 10.0, 0.0) == pytest.approx(0.0)


def test_lerp_end() -> None:
    assert lerp(0.0, 10.0, 1.0) == pytest.approx(10.0)


def test_lerp_midpoint() -> None:
    assert lerp(0.0, 10.0, 0.5) == pytest.approx(5.0)


def test_lerp_negative_range() -> None:
    assert lerp(10.0, 0.0, 0.25) == pytest.approx(7.5)


# ---------------------------------------------------------------------------
# lerp_color
# ---------------------------------------------------------------------------


def test_lerp_color_at_zero_returns_c1() -> None:
    assert lerp_color(0xFF0000, 0x0000FF, 0.0) == 0xFF0000


def test_lerp_color_at_one_returns_c2() -> None:
    assert lerp_color(0xFF0000, 0x0000FF, 1.0) == 0x0000FF


def test_lerp_color_midpoint_red_to_blue() -> None:
    mid = lerp_color(0xFF0000, 0x0000FF, 0.5)
    r = (mid >> 16) & 0xFF
    g = (mid >> 8) & 0xFF
    b = mid & 0xFF
    assert r == pytest.approx(128, abs=1)
    assert g == 0
    assert b == pytest.approx(128, abs=1)


def test_lerp_color_clamps_t() -> None:
    assert lerp_color(0xFF0000, 0x0000FF, -0.5) == 0xFF0000
    assert lerp_color(0xFF0000, 0x0000FF, 1.5) == 0x0000FF


def test_lerp_color_same_color() -> None:
    assert lerp_color(0x4FC3F7, 0x4FC3F7, 0.5) == 0x4FC3F7


# ---------------------------------------------------------------------------
# pulse_scale
# ---------------------------------------------------------------------------


def test_pulse_scale_at_zero() -> None:
    assert pulse_scale(0.0, 1.0) == pytest.approx(1.0)


def test_pulse_scale_peak_at_half_duration() -> None:
    peak = pulse_scale(0.5, 1.0, amplitude=0.25)
    assert peak == pytest.approx(1.25)


def test_pulse_scale_at_duration() -> None:
    assert pulse_scale(1.0, 1.0) == pytest.approx(1.0)


def test_pulse_scale_beyond_duration() -> None:
    assert pulse_scale(2.0, 1.0) == pytest.approx(1.0)


def test_pulse_scale_zero_duration() -> None:
    assert pulse_scale(0.5, 0.0) == pytest.approx(1.0)


def test_pulse_scale_custom_amplitude() -> None:
    peak = pulse_scale(0.5, 1.0, amplitude=0.5)
    assert peak == pytest.approx(1.5)


def test_pulse_scale_values_finite() -> None:
    for t in [0.0, 0.1, 0.25, 0.5, 0.75, 0.99, 1.0, 1.5]:
        assert math.isfinite(pulse_scale(t, 1.0))
