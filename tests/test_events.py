"""Tests for biopulse.model.events.EventStream."""

from __future__ import annotations

import pytest

from biopulse.model.events import EventStream
from biopulse.model.schema import Event
from biopulse.model.schema import EventStream as EventStreamSchema


def _event(t: float, node: str = "X", state: int = 1) -> Event:
    return Event(t=t, node=node, state=state)


def test_empty_stream() -> None:
    es = EventStream()
    assert len(es) == 0
    assert not es
    assert es.duration == 0.0


def test_stream_from_list() -> None:
    es = EventStream([_event(1.0), _event(0.5), _event(2.0)])
    assert len(es) == 3
    assert bool(es)


def test_stream_from_schema_envelope() -> None:
    envelope = EventStreamSchema.model_validate({"events": [{"t": 1.0, "node": "A", "state": 1}]})
    es = EventStream(envelope)
    assert len(es) == 1


def test_sorted_on_construction() -> None:
    times = [3.0, 1.0, 2.0]
    es = EventStream([_event(t) for t in times])
    assert [e.t for e in es] == [1.0, 2.0, 3.0]


def test_duration() -> None:
    es = EventStream([_event(0.5), _event(2.5)])
    assert es.duration == 2.5


def test_iteration_order() -> None:
    events = [_event(t) for t in [0.2, 0.8, 1.5]]
    es = EventStream(reversed(events))
    result_times = [e.t for e in es]
    assert result_times == [0.2, 0.8, 1.5]


def test_at_or_before_all() -> None:
    es = EventStream([_event(0.0), _event(1.0), _event(2.0)])
    assert len(es.at_or_before(2.0)) == 3


def test_at_or_before_partial() -> None:
    es = EventStream([_event(0.0), _event(1.0), _event(2.0)])
    result = es.at_or_before(1.0)
    assert [e.t for e in result] == [0.0, 1.0]


def test_at_or_before_none() -> None:
    es = EventStream([_event(1.0), _event(2.0)])
    assert es.at_or_before(0.5) == []


def test_after() -> None:
    es = EventStream([_event(0.0), _event(1.0), _event(2.0)])
    result = es.after(1.0)
    assert [e.t for e in result] == [2.0]


def test_between_inclusive() -> None:
    es = EventStream([_event(t) for t in [0.0, 1.0, 2.0, 3.0]])
    result = es.between(1.0, 2.0)
    assert [e.t for e in result] == [1.0, 2.0]


def test_between_invalid_range() -> None:
    es = EventStream([_event(1.0)])
    with pytest.raises(ValueError, match="t1"):
        es.between(2.0, 1.0)


def test_between_empty_range() -> None:
    es = EventStream([_event(0.0), _event(3.0)])
    assert es.between(1.0, 2.0) == []
