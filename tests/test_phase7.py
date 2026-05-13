"""Phase 7 tests: advanced visual effect traitlets and new interp utilities."""

from __future__ import annotations

import pytest

from biopulse.core.animation.interp import (
    heatmap_color,
    ring_alpha,
    ring_progress,
    ring_radius,
)
from biopulse.core.renderer.widget import GraphWidget, PlayWidget

# ===========================================================================
# New interp utilities
# ===========================================================================


class TestRingProgress:
    def test_zero_at_start(self) -> None:
        assert ring_progress(0.0, 1.0) == pytest.approx(0.0)

    def test_one_at_duration(self) -> None:
        assert ring_progress(1.0, 1.0) == pytest.approx(1.0)

    def test_clamped_below_zero(self) -> None:
        assert ring_progress(-0.5, 1.0) == pytest.approx(0.0)

    def test_clamped_above_one(self) -> None:
        assert ring_progress(2.0, 1.0) == pytest.approx(1.0)

    def test_midpoint(self) -> None:
        assert ring_progress(0.5, 1.0) == pytest.approx(0.5)

    def test_zero_duration_returns_one(self) -> None:
        assert ring_progress(0.0, 0.0) == pytest.approx(1.0)


class TestRingAlpha:
    def test_peak_at_start(self) -> None:
        assert ring_alpha(0.0, 1.0, peak=0.7) == pytest.approx(0.7)

    def test_zero_at_end(self) -> None:
        assert ring_alpha(1.0, 1.0) == pytest.approx(0.0)

    def test_default_peak(self) -> None:
        assert ring_alpha(0.0, 1.0) == pytest.approx(0.7)

    def test_midpoint_half_peak(self) -> None:
        assert ring_alpha(0.5, 1.0, peak=1.0) == pytest.approx(0.5)

    def test_non_negative(self) -> None:
        assert ring_alpha(2.0, 1.0) >= 0.0


class TestRingRadius:
    def test_base_at_start(self) -> None:
        assert ring_radius(0.0, 1.0, base=12.0) == pytest.approx(12.0)

    def test_expanded_at_end(self) -> None:
        r = ring_radius(1.0, 1.0, base=12.0, expansion=2.5)
        assert r == pytest.approx(12.0 * (1.0 + 2.5))

    def test_monotonically_increasing(self) -> None:
        radii = [ring_radius(t / 10, 1.0, base=10.0) for t in range(11)]
        assert all(radii[i] <= radii[i + 1] for i in range(len(radii) - 1))


class TestHeatmapColor:
    def test_zero_activations_returns_cold(self) -> None:
        cold = 0x2D5986
        assert heatmap_color(0, 10, cold=cold, hot=0xFF9A00) == cold

    def test_max_activations_returns_hot(self) -> None:
        hot = 0xFF9A00
        assert heatmap_color(10, 10, cold=0x2D5986, hot=hot) == hot

    def test_zero_max_returns_cold(self) -> None:
        cold = 0x2D5986
        assert heatmap_color(5, 0, cold=cold) == cold

    def test_intermediate_is_between(self) -> None:
        cold = 0x000000
        hot = 0xFFFFFF
        mid = heatmap_color(5, 10, cold=cold, hot=hot)
        # Each channel should be around 128 (half of 255)
        r = (mid >> 16) & 0xFF
        assert 100 < r < 155

    def test_negative_count_returns_cold(self) -> None:
        cold = 0x2D5986
        assert heatmap_color(-1, 10, cold=cold) == cold

    def test_over_max_clamped(self) -> None:
        hot = 0xFF9A00
        assert heatmap_color(20, 10, hot=hot) == hot

    def test_default_colors(self) -> None:
        result = heatmap_color(10, 10)
        assert isinstance(result, int)
        assert 0 <= result <= 0xFFFFFF


# ===========================================================================
# GraphWidget Phase 7 traitlets
# ===========================================================================


class TestGraphWidgetPhase7:
    def test_glow_enabled_default_false(self) -> None:
        w = GraphWidget()
        assert w.glow_enabled is False

    def test_glow_enabled_settable(self) -> None:
        w = GraphWidget()
        w.glow_enabled = True
        assert w.glow_enabled is True

    def test_glow_enabled_constructor(self) -> None:
        w = GraphWidget(glow_enabled=True)
        assert w.glow_enabled is True


# ===========================================================================
# PlayWidget Phase 7 traitlets
# ===========================================================================


class TestPlayWidgetPhase7:
    def test_glow_enabled_default_true(self) -> None:
        w = PlayWidget()
        assert w.glow_enabled is True

    def test_pulse_ring_enabled_default_true(self) -> None:
        w = PlayWidget()
        assert w.pulse_ring_enabled is True

    def test_heatmap_enabled_default_false(self) -> None:
        w = PlayWidget()
        assert w.heatmap_enabled is False

    def test_particles_enabled_default_false(self) -> None:
        w = PlayWidget()
        assert w.particles_enabled is False

    def test_glow_settable(self) -> None:
        w = PlayWidget()
        w.glow_enabled = False
        assert w.glow_enabled is False

    def test_pulse_ring_settable(self) -> None:
        w = PlayWidget()
        w.pulse_ring_enabled = False
        assert w.pulse_ring_enabled is False

    def test_heatmap_enabled_settable(self) -> None:
        w = PlayWidget()
        w.heatmap_enabled = True
        assert w.heatmap_enabled is True

    def test_particles_settable(self) -> None:
        w = PlayWidget()
        w.particles_enabled = True
        assert w.particles_enabled is True

    def test_all_effects_via_constructor(self) -> None:
        w = PlayWidget(
            glow_enabled=False,
            pulse_ring_enabled=False,
            heatmap_enabled=True,
            particles_enabled=True,
        )
        assert w.glow_enabled is False
        assert w.pulse_ring_enabled is False
        assert w.heatmap_enabled is True
        assert w.particles_enabled is True
