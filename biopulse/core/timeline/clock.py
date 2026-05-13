"""Logical playback clock — pure state machine, no side effects."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

ClockState = Literal["idle", "playing", "paused"]


@dataclass
class Clock:
    """Playback clock that tracks time and play/pause/seek state.

    All time values are in seconds. The clock has no knowledge of events or
    rendering — it is a pure time-state machine used by :class:`Scheduler`
    and the animation loop.
    """

    speed: float = 1.0
    _state: ClockState = field(default="idle", repr=False, compare=False)
    _t: float = field(default=0.0, repr=False, compare=False)

    @property
    def state(self) -> ClockState:
        return self._state

    @property
    def t(self) -> float:
        return self._t

    def play(self) -> None:
        """Start or resume playback."""
        self._state = "playing"

    def pause(self) -> None:
        """Pause playback, preserving the current time."""
        if self._state == "playing":
            self._state = "paused"

    def stop(self) -> None:
        """Stop playback and reset time to 0."""
        self._state = "idle"
        self._t = 0.0

    def seek(self, t: float) -> None:
        """Jump to time *t* without changing play/pause state."""
        if t < 0:
            raise ValueError(f"seek time must be >= 0, got {t}")
        self._t = t

    def tick(self, delta: float) -> float:
        """Advance the clock by *delta* real seconds (scaled by :attr:`speed`).

        Returns the new time. No-op if not playing.
        """
        if delta < 0:
            raise ValueError(f"tick delta must be >= 0, got {delta}")
        if self._state != "playing":
            return self._t
        self._t += delta * self.speed
        return self._t
