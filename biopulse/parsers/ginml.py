"""Parser for GINML — GINsim's native XML graph format.

GINML is produced by `GINsim <http://ginsim.org/>`_ and encodes a logical
regulatory graph.  The relevant structure::

    <GINsim-model id="...">
      <nodelist>
        <node id="A" maxvalue="1" .../>
      </nodelist>
      <edgelist>
        <edge from="A" to="B" minvalue="1" sign="positive"/>
      </edgelist>
    </GINsim-model>

``sign`` values: ``positive`` → activation, ``negative`` → inhibition.
If ``sign`` is absent, the edge type defaults to ``"activation"``.

Node ``nodeclass`` attribute, if present, is stored as the ``group`` field.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from biopulse.model.graph import Graph
from biopulse.model.schema import Graph as GraphSchema

_SIGN_MAP = {"positive": "activation", "negative": "inhibition"}


def parse_ginml(source: str | Path) -> Graph:
    """Parse a GINML file and return a :class:`~biopulse.model.graph.Graph`.

    Args:
        source: File path or ``pathlib.Path`` to a ``.ginml`` file.

    Returns:
        A :class:`~biopulse.model.graph.Graph` with nodes and signed edges.

    Raises:
        ValueError: If the root element is not a GINsim model, or if an edge
            references an unknown sign value.
    """
    tree = ET.parse(str(source))
    root = tree.getroot()

    # Strip namespace prefix if present
    tag = root.tag.split("}")[-1] if "}" in root.tag else root.tag
    if not tag.startswith("GINsim"):
        raise ValueError(f"Expected a GINsim-model root element, got <{root.tag}>")

    def _find(parent: ET.Element, *local_names: str) -> ET.Element | None:
        for ln in local_names:
            for child in parent:
                ctag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                if ctag == ln:
                    return child
        return None

    def _findall(parent: ET.Element, local_name: str) -> list[ET.Element]:
        results = []
        for child in parent:
            ctag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if ctag == local_name:
                results.append(child)
        return results

    node_dicts: list[dict[str, str]] = []
    nodelist = _find(root, "nodelist")
    if nodelist is not None:
        for node_el in _findall(nodelist, "node"):
            nid = node_el.get("id")
            if not nid:
                continue
            entry: dict[str, str] = {"id": nid}
            nodeclass = node_el.get("nodeclass")
            if nodeclass:
                entry["group"] = nodeclass
            node_dicts.append(entry)

    edge_dicts: list[dict[str, str]] = []
    edgelist = _find(root, "edgelist")
    if edgelist is not None:
        for edge_el in _findall(edgelist, "edge"):
            src = edge_el.get("from")
            tgt = edge_el.get("to")
            if not src or not tgt:
                continue
            raw_sign = edge_el.get("sign", "positive")
            etype = _SIGN_MAP.get(raw_sign)
            if etype is None:
                raise ValueError(
                    f"Unknown GINML edge sign {raw_sign!r}; expected 'positive' or 'negative'."
                )
            edge_dicts.append({"source": src, "target": tgt, "type": etype})

    schema = GraphSchema.model_validate({"nodes": node_dicts, "edges": edge_dicts})
    return Graph(schema)
