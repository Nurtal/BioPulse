"""Tests for biopulse.core.timeline.scheduler.Scheduler."""

from __future__ import annotations

import pytest

from biopulse.core.timeline.scheduler import Scheduler
from biopulse.model.events import EventStream
from biopulse.model.schema import Event


def _ev(t: float, node: str = "X", state: int = 1) -> Event:
    return Event(t=t, node=node, state=state)


def _stream(*events: Event) -> EventStream:
    return EventStream(list(events))


def test_events_in_window_basic() -> None:
    s = Scheduler(_stream(_ev(0.0), _ev(1.0), _ev(2.0)))
    result = s.events_in_window(0.0, 1.5)
    assert [e.t for e in result] == [1.0]


def test_events_in_window_exclusive_lower() -> None:
    s = Scheduler(_stream(_ev(1.0), _ev(2.0), _ev(3.0)))
    result = s.events_in_window(1.0, 3.0)
    assert [e.t for e in result] == [2.0, 3.0]


def test_events_in_window_inclusive_upper() -> None:
    s = Scheduler(_stream(_ev(1.0), _ev(2.0)))
    result = s.events_in_window(0.5, 2.0)
    assert [e.t for e in result] == [1.0, 2.0]


def test_events_in_window_empty_range() -> None:
    s = Scheduler(_stream(_ev(1.0)))
    assert s.events_in_window(1.5, 2.0) == []


def test_events_in_window_bad_range() -> None:
    s = Scheduler(_stream(_ev(1.0)))
    with pytest.raises(ValueError, match="t1"):
        s.events_in_window(2.0, 1.0)


def test_events_in_window_empty_stream() -> None:
    s = Scheduler(EventStream())
    assert s.events_in_window(0.0, 5.0) == []


def test_active_events_at_latest_per_node() -> None:
    stream = _stream(
        _ev(0.5, "A", 1),
        _ev(1.0, "A", 0),
        _ev(0.5, "B", 1),
    )
    s = Scheduler(stream)
    active = s.active_events_at(2.0)
    active_map = {e.node: e for e in active}
    assert active_map["A"].state == 0
    assert active_map["A"].t == pytest.approx(1.0)
    assert active_map["B"].state == 1


def test_active_events_at_excludes_future() -> None:
    stream = _stream(_ev(0.5, "A", 1), _ev(2.0, "A", 0))
    s = Scheduler(stream)
    active = s.active_events_at(1.0)
    assert len(active) == 1
    assert active[0].state == 1


def test_active_events_at_empty_before_first_event() -> None:
    s = Scheduler(_stream(_ev(1.0)))
    assert s.active_events_at(0.5) == []


def test_events_at_tolerance() -> None:
    s = Scheduler(_stream(_ev(1.0), _ev(2.0), _ev(3.0)))
    result = s.events_at(2.0)
    assert len(result) == 1
    assert result[0].t == pytest.approx(2.0)
