"""Layout protocol — the interface every layout algorithm must satisfy."""

from __future__ import annotations

from typing import Protocol

from biopulse.model.graph import Graph


class Layout(Protocol):
    def compute(self, graph: Graph) -> dict[str, tuple[float, float]]:
        """Return 2-D positions for every node in *graph*.

        Keys are node ids; values are ``(x, y)`` floats in an arbitrary
        coordinate space (callers normalise to canvas pixels).
        """
        ...
