"""Load BioPulse canonical JSON files into validated runtime types."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from biopulse.model.events import EventStream
from biopulse.model.graph import Graph
from biopulse.model.schema import EventStream as EventStreamSchema
from biopulse.model.schema import Graph as GraphSchema
from biopulse.model.schema import Scene


def _read_json(path: Path | str) -> Any:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_graph(path: Path | str) -> Graph:
    """Load a graph-only JSON file (``{"nodes": [...], "edges": [...]}``).

    Returns a :class:`~biopulse.model.graph.Graph` backed by a NetworkX DiGraph.
    Raises :class:`pydantic.ValidationError` on schema violations.
    """
    data = _read_json(path)
    return Graph(GraphSchema.model_validate(data))


def load_events(path: Path | str) -> EventStream:
    """Load an events-only JSON file (``{"events": [...]}``).

    Returns a time-sorted :class:`~biopulse.model.events.EventStream`.
    Node references are **not** validated here because no graph is available;
    cross-validation happens in :func:`load_scene`.
    """
    data = _read_json(path)
    envelope = EventStreamSchema.model_validate(data)
    return EventStream(envelope)


def load_scene(path: Path | str) -> tuple[Graph, EventStream]:
    """Load a scene JSON file (``{"graph": {...}, "events": [...]}``).

    Returns a ``(Graph, EventStream)`` tuple. Event-node cross-validation is
    performed by the :class:`~biopulse.model.schema.Scene` model: any event
    referencing an unknown node raises :class:`pydantic.ValidationError`.
    """
    data = _read_json(path)
    scene = Scene.model_validate(data)
    return Graph(scene.graph), EventStream(scene.events)
