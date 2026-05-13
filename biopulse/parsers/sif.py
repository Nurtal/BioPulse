"""Parser for the Simple Interaction Format (SIF).

SIF is a line-oriented text format used by Cytoscape and common in the Boolean
network community.  Each non-comment line describes one or more interactions::

    source  interactionType  target1  target2 ...

Columns are separated by whitespace (spaces or tabs).  Lines starting with
``#`` and blank lines are ignored.

Interaction type mapping (case-insensitive):

=========================  =============
SIF type strings           BioPulse type
=========================  =============
1, a, +, activates,        activation
activate, activation, ->
-1, i, -, inhibits,        inhibition
inhibit, inhibition, -|
=========================  =============

Unknown type strings raise :class:`ValueError` unless *default_type* is given.
"""

from __future__ import annotations

from pathlib import Path
from typing import TextIO

from biopulse.model.graph import Graph
from biopulse.model.schema import Graph as GraphSchema

_ACTIVATION_TOKENS = frozenset({"1", "a", "+", "activates", "activate", "activation", "->"})
_INHIBITION_TOKENS = frozenset({"-1", "i", "-", "inhibits", "inhibit", "inhibition", "-|"})


def _map_type(raw: str, default_type: str | None) -> str:
    tok = raw.strip().lower()
    if tok in _ACTIVATION_TOKENS:
        return "activation"
    if tok in _INHIBITION_TOKENS:
        return "inhibition"
    if default_type is not None:
        return default_type
    raise ValueError(
        f"Unknown SIF interaction type {raw!r}. "
        "Pass default_type='activation' or 'inhibition' to accept unknown types."
    )


def parse_sif(
    source: str | Path | TextIO,
    *,
    default_type: str | None = None,
) -> Graph:
    """Parse a SIF file or string and return a :class:`~biopulse.model.graph.Graph`.

    Args:
        source: File path, ``pathlib.Path``, or an open text stream.
        default_type: Fallback edge type (``"activation"`` or ``"inhibition"``)
            for interaction strings not in the built-in mapping.  If ``None``
            (default), unknown strings raise :class:`ValueError`.

    Returns:
        A :class:`~biopulse.model.graph.Graph` with all nodes and edges found
        in the file.  Duplicate nodes are silently deduplicated; duplicate edges
        are also deduplicated (first occurrence wins).
    """
    if default_type is not None and default_type not in ("activation", "inhibition"):
        raise ValueError(f"default_type must be 'activation' or 'inhibition', got {default_type!r}")

    lines: list[str]
    if isinstance(source, (str, Path)):
        lines = Path(source).read_text(encoding="utf-8").splitlines()
    else:
        lines = source.read().splitlines()

    node_ids: list[str] = []
    seen_nodes: set[str] = set()
    edge_dicts: list[dict[str, str]] = []
    seen_edges: set[tuple[str, str]] = set()

    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 3:
            raise ValueError(
                f"SIF line must have at least 3 columns (source type target), got: {raw_line!r}"
            )
        src, itype, *targets = parts
        edge_type = _map_type(itype, default_type)

        for nid in [src, *targets]:
            if nid not in seen_nodes:
                node_ids.append(nid)
                seen_nodes.add(nid)

        for tgt in targets:
            key = (src, tgt)
            if key not in seen_edges:
                edge_dicts.append({"source": src, "target": tgt, "type": edge_type})
                seen_edges.add(key)

    schema = GraphSchema.model_validate(
        {"nodes": [{"id": nid} for nid in node_ids], "edges": edge_dicts}
    )
    return Graph(schema)
