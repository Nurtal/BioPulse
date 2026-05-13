"""Canonical wire-format Pydantic v2 models for BioPulse.

All parsers convert their input format into these models. The renderer
consumes only these models. This module is the single source of truth for
the JSON schema BioPulse exchanges with the outside world.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

EdgeType = Literal["activation", "inhibition"]


class Node(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    group: str | None = None


class Edge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str = Field(min_length=1)
    target: str = Field(min_length=1)
    type: EdgeType


class Graph(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nodes: list[Node]
    edges: list[Edge] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_consistency(self) -> Graph:
        seen: set[str] = set()
        for node in self.nodes:
            if node.id in seen:
                raise ValueError(f"duplicate node id: {node.id!r}")
            seen.add(node.id)
        for edge in self.edges:
            if edge.source not in seen:
                raise ValueError(f"edge source {edge.source!r} not in nodes")
            if edge.target not in seen:
                raise ValueError(f"edge target {edge.target!r} not in nodes")
        return self


class Event(BaseModel):
    """A single state-change event at time `t`."""

    model_config = ConfigDict(extra="forbid")

    t: float = Field(ge=0)
    node: str = Field(min_length=1)
    state: int


class EventStream(BaseModel):
    """Wire envelope for a standalone events file: ``{"events": [...]}``.

    For the operational sorted/bisect container see `biopulse.model.events.EventStream`.
    """

    model_config = ConfigDict(extra="forbid")

    events: list[Event] = Field(default_factory=list)


class Scene(BaseModel):
    """Combined graph + event timeline — the primary end-to-end wire format."""

    model_config = ConfigDict(extra="forbid")

    graph: Graph
    events: list[Event] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_events_reference_nodes(self) -> Scene:
        ids = {n.id for n in self.graph.nodes}
        for event in self.events:
            if event.node not in ids:
                raise ValueError(f"event references unknown node: {event.node!r}")
        return self
