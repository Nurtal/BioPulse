"""Force-directed layout using NetworkX spring (Fruchterman-Reingold) algorithm.

Named ForceAtlasLayout as a placeholder for the FA2 algorithm (``fa2`` package)
which can be dropped in later without changing the public interface.
"""

from __future__ import annotations

import networkx as nx

from biopulse.model.graph import Graph


class ForceAtlasLayout:
    """2-D force-directed layout wrapping ``networkx.spring_layout``.

    Args:
        seed: Random seed for reproducible layouts. ``None`` for random.
        k: Optimal distance between nodes (``None`` = 1/sqrt(n)).
        iterations: Number of spring simulation steps.
    """

    def __init__(
        self,
        seed: int | None = 42,
        k: float | None = None,
        iterations: int = 50,
    ) -> None:
        self.seed = seed
        self.k = k
        self.iterations = iterations

    def compute(self, graph: Graph) -> dict[str, tuple[float, float]]:
        """Return ``{node_id: (x, y)}`` positions in ``[-1, 1]`` space."""
        g = graph.digraph
        if len(g) == 0:
            return {}
        pos: dict[str, tuple[float, float]] = {
            node: (float(xy[0]), float(xy[1]))
            for node, xy in nx.spring_layout(
                g,
                seed=self.seed,
                k=self.k,
                iterations=self.iterations,
            ).items()
        }
        return pos
