"""Graph — runtime wrapper around networkx.DiGraph built from the canonical schema."""

from __future__ import annotations

from typing import Any

import networkx as nx

from biopulse.model.schema import Graph as GraphSchema


class Graph:
    """Operational graph built from a canonical :class:`~biopulse.model.schema.Graph`.

    Stores the original schema for serialization and a ``networkx.DiGraph``
    for traversal and layout algorithms.
    """

    __slots__ = ("_digraph", "_schema")

    def __init__(self, schema: GraphSchema) -> None:
        self._schema = schema
        self._digraph: nx.DiGraph = self._build(schema)

    @staticmethod
    def _build(schema: GraphSchema) -> nx.DiGraph:
        g: nx.DiGraph = nx.DiGraph()
        for node in schema.nodes:
            attrs: dict[str, Any] = {}
            if node.group is not None:
                attrs["group"] = node.group
            g.add_node(node.id, **attrs)
        for edge in schema.edges:
            g.add_edge(edge.source, edge.target, type=edge.type)
        return g

    @property
    def schema(self) -> GraphSchema:
        return self._schema

    @property
    def digraph(self) -> nx.DiGraph:
        return self._digraph

    @property
    def node_ids(self) -> list[str]:
        return [n.id for n in self._schema.nodes]

    def __len__(self) -> int:
        return len(self._schema.nodes)

    def __contains__(self, node_id: object) -> bool:
        return bool(self._digraph.has_node(node_id))

    def __repr__(self) -> str:
        return f"Graph(nodes={len(self)}, edges={len(self._digraph.edges())})"
