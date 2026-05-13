"""Scheduler — dispatches events from an EventStream as playback time advances."""

from __future__ import annotations

from biopulse.model.events import EventStream
from biopulse.model.schema import Event


class Scheduler:
    """Maps clock time to the events that should fire at that time.

    Designed to be used alongside :class:`~biopulse.core.timeline.clock.Clock`:

    * :meth:`events_in_window` is called each tick with the previous and
      current clock times to get newly-active events.
    * :meth:`active_events_at` is called on seek to reconstruct the full
      node-state snapshot at an arbitrary time.
    """

    def __init__(self, stream: EventStream) -> None:
        self._stream = stream

    @property
    def stream(self) -> EventStream:
        return self._stream

    def events_in_window(self, t0: float, t1: float) -> list[Event]:
        """Events with ``t0 < e.t <= t1`` — newly active in this time step.

        Call this from the animation tick loop with ``t0 = previous_t`` and
        ``t1 = current_t``.
        """
        if t1 < t0:
            raise ValueError(f"t1 ({t1}) must be >= t0 ({t0})")
        return [e for e in self._stream.between(t0, t1) if e.t > t0]

    def active_events_at(self, t: float) -> list[Event]:
        """The latest event per node with ``e.t <= t``.

        Returns the current state of every node that has fired at least once
        by time *t*. Use this on seek to reconstruct the full scene state.
        """
        latest: dict[str, Event] = {}
        for event in self._stream.at_or_before(t):
            if event.node not in latest or event.t >= latest[event.node].t:
                latest[event.node] = event
        return list(latest.values())

    def events_at(self, t: float, tol: float = 1e-9) -> list[Event]:
        """Events within *tol* of exactly time *t*."""
        return self._stream.between(t - tol, t + tol)
