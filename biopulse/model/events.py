"""EventStream — sorted, iterable, bisect-seekable container for events.

Events are kept sorted by ``t`` so the renderer can seek to any moment in
O(log n) and stream events forward in O(1) per event.
"""

from __future__ import annotations

import bisect
from collections.abc import Iterable, Iterator

from biopulse.model.schema import Event
from biopulse.model.schema import EventStream as EventStreamSchema


class EventStream:
    """Time-sorted event sequence with O(log n) seek by ``t``.

    Accepts either an iterable of :class:`~biopulse.model.schema.Event` objects
    or a validated :class:`~biopulse.model.schema.EventStream` wire model.
    """

    __slots__ = ("_events", "_times")

    def __init__(self, events: Iterable[Event] | EventStreamSchema = ()) -> None:
        if isinstance(events, EventStreamSchema):
            raw: Iterable[Event] = events.events
        else:
            raw = events
        self._events: list[Event] = sorted(raw, key=lambda e: e.t)
        self._times: list[float] = [e.t for e in self._events]

    def __iter__(self) -> Iterator[Event]:
        return iter(self._events)

    def __len__(self) -> int:
        return len(self._events)

    def __bool__(self) -> bool:
        return bool(self._events)

    @property
    def duration(self) -> float:
        """Time of the last event, or 0.0 for an empty stream."""
        return self._times[-1] if self._times else 0.0

    def at_or_before(self, t: float) -> list[Event]:
        """All events with ``e.t <= t``, in chronological order."""
        idx = bisect.bisect_right(self._times, t)
        return list(self._events[:idx])

    def after(self, t: float) -> list[Event]:
        """All events with ``e.t > t``, in chronological order."""
        idx = bisect.bisect_right(self._times, t)
        return list(self._events[idx:])

    def between(self, t0: float, t1: float) -> list[Event]:
        """Events with ``t0 <= e.t <= t1``, in chronological order."""
        if t1 < t0:
            raise ValueError(f"t1 ({t1}) must be >= t0 ({t0})")
        lo = bisect.bisect_left(self._times, t0)
        hi = bisect.bisect_right(self._times, t1)
        return list(self._events[lo:hi])
