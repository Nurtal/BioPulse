"""Per-node visual animation state."""

from __future__ import annotations

from dataclasses import dataclass

from biopulse.model.schema import Event


@dataclass
class NodeVisualState:
    """Snapshot of one node's visual state at the current playback time."""

    active: bool = False
    t_changed: float = 0.0
    prev_active: bool = False


class AnimationState:
    """Tracks :class:`NodeVisualState` for every node as events are applied.

    Intended usage::

        state = AnimationState(graph.node_ids)
        for event in scheduler.events_in_window(prev_t, current_t):
            state.apply(event)
        color = compute_color(state.get("STAT3"), current_t)
    """

    def __init__(self, node_ids: list[str]) -> None:
        self._states: dict[str, NodeVisualState] = {nid: NodeVisualState() for nid in node_ids}

    def apply(self, event: Event) -> None:
        """Apply a state-change event, updating the affected node."""
        if event.node not in self._states:
            raise KeyError(f"unknown node: {event.node!r}")
        cur = self._states[event.node]
        self._states[event.node] = NodeVisualState(
            active=bool(event.state),
            t_changed=event.t,
            prev_active=cur.active,
        )

    def get(self, node_id: str) -> NodeVisualState:
        """Return the current visual state for *node_id*."""
        return self._states[node_id]

    def reset(self) -> None:
        """Reset all nodes to the initial (inactive) state."""
        for nid in self._states:
            self._states[nid] = NodeVisualState()

    @property
    def node_ids(self) -> list[str]:
        return list(self._states)
