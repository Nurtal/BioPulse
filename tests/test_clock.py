"""Tests for biopulse.core.timeline.clock.Clock."""

from __future__ import annotations

import pytest

from biopulse.core.timeline.clock import Clock


def test_initial_state() -> None:
    c = Clock()
    assert c.state == "idle"
    assert c.t == 0.0
    assert c.speed == 1.0


def test_play_changes_state() -> None:
    c = Clock()
    c.play()
    assert c.state == "playing"


def test_play_from_paused() -> None:
    c = Clock()
    c.play()
    c.pause()
    c.play()
    assert c.state == "playing"


def test_pause_requires_playing() -> None:
    c = Clock()
    c.pause()
    assert c.state == "idle"


def test_pause_stops_playing() -> None:
    c = Clock()
    c.play()
    c.pause()
    assert c.state == "paused"


def test_stop_resets_time() -> None:
    c = Clock()
    c.play()
    c.tick(2.5)
    c.stop()
    assert c.state == "idle"
    assert c.t == 0.0


def test_tick_advances_when_playing() -> None:
    c = Clock()
    c.play()
    t = c.tick(1.0)
    assert t == pytest.approx(1.0)
    assert c.t == pytest.approx(1.0)


def test_tick_noop_when_idle() -> None:
    c = Clock()
    t = c.tick(1.0)
    assert t == 0.0
    assert c.t == 0.0


def test_tick_noop_when_paused() -> None:
    c = Clock()
    c.play()
    c.tick(1.0)
    c.pause()
    c.tick(99.0)
    assert c.t == pytest.approx(1.0)


def test_tick_speed_multiplier() -> None:
    c = Clock(speed=2.0)
    c.play()
    c.tick(1.0)
    assert c.t == pytest.approx(2.0)


def test_tick_fractional_speed() -> None:
    c = Clock(speed=0.5)
    c.play()
    c.tick(4.0)
    assert c.t == pytest.approx(2.0)


def test_tick_accumulates() -> None:
    c = Clock()
    c.play()
    c.tick(1.0)
    c.tick(0.5)
    c.tick(0.25)
    assert c.t == pytest.approx(1.75)


def test_seek_changes_time() -> None:
    c = Clock()
    c.seek(3.14)
    assert c.t == pytest.approx(3.14)


def test_seek_preserves_state() -> None:
    c = Clock()
    c.play()
    c.seek(2.0)
    assert c.state == "playing"


def test_seek_negative_raises() -> None:
    c = Clock()
    with pytest.raises(ValueError, match="seek time"):
        c.seek(-1.0)


def test_tick_negative_delta_raises() -> None:
    c = Clock()
    c.play()
    with pytest.raises(ValueError, match="delta"):
        c.tick(-0.1)
