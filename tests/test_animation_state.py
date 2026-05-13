"""Tests for biopulse.core.animation.state.AnimationState."""

from __future__ import annotations

import pytest

from biopulse.core.animation.state import AnimationState, NodeVisualState
from biopulse.model.schema import Event


def _ev(node: str, state: int, t: float = 0.0) -> Event:
    return Event(t=t, node=node, state=state)


def test_initial_state_inactive() -> None:
    s = AnimationState(["A", "B"])
    assert s.get("A").active is False
    assert s.get("B").active is False


def test_apply_activates_node() -> None:
    s = AnimationState(["X"])
    s.apply(_ev("X", 1, t=1.5))
    assert s.get("X").active is True
    assert s.get("X").t_changed == pytest.approx(1.5)


def test_apply_deactivates_node() -> None:
    s = AnimationState(["X"])
    s.apply(_ev("X", 1, t=1.0))
    s.apply(_ev("X", 0, t=2.0))
    assert s.get("X").active is False
    assert s.get("X").t_changed == pytest.approx(2.0)


def test_apply_tracks_prev_active() -> None:
    s = AnimationState(["X"])
    s.apply(_ev("X", 1, t=1.0))
    s.apply(_ev("X", 0, t=2.0))
    assert s.get("X").prev_active is True


def test_apply_unknown_node_raises() -> None:
    s = AnimationState(["A"])
    with pytest.raises(KeyError, match="unknown node"):
        s.apply(_ev("GHOST", 1))


def test_reset_clears_all() -> None:
    s = AnimationState(["A", "B"])
    s.apply(_ev("A", 1, t=1.0))
    s.reset()
    assert s.get("A") == NodeVisualState()
    assert s.get("B") == NodeVisualState()


def test_node_ids() -> None:
    s = AnimationState(["C", "A", "B"])
    assert set(s.node_ids) == {"A", "B", "C"}


def test_multiple_nodes_independent() -> None:
    s = AnimationState(["A", "B", "C"])
    s.apply(_ev("A", 1, t=0.5))
    s.apply(_ev("C", 1, t=1.0))
    assert s.get("A").active is True
    assert s.get("B").active is False
    assert s.get("C").active is True
