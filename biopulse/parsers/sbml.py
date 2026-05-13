"""Parser for SBML Level 3 + qual package.

The SBML qual extension encodes qualitative (Boolean/multi-valued) models.
This parser uses only the standard library ``xml.etree.ElementTree`` — no
``python-libsbml`` dependency is required.

Relevant XML structure::

    <sbml xmlns="..." xmlns:qual="...qual/version1">
      <model>
        <qual:listOfQualitativeSpecies>
          <qual:qualitativeSpecies qual:id="A" qual:compartment="nucleus"/>
        </qual:listOfQualitativeSpecies>
        <qual:listOfTransitions>
          <qual:transition qual:id="tr_B">
            <qual:listOfInputs>
              <qual:input qual:qualitativeSpecies="A" qual:sign="positive"/>
            </qual:listOfInputs>
            <qual:listOfOutputs>
              <qual:output qual:qualitativeSpecies="B"/>
            </qual:listOfOutputs>
          </qual:transition>
        </qual:listOfTransitions>
      </model>
    </sbml>

Each transition produces one edge **per (input, output) pair** with the sign
of the input (``positive`` → activation, ``negative`` → inhibition,
``unknown`` or absent → activation).

The ``qual:compartment`` attribute of a qualitative species, when present, is
stored as the node ``group``.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from biopulse.model.graph import Graph
from biopulse.model.schema import Graph as GraphSchema

_QUAL_NS = "http://www.sbml.org/sbml/level3/version1/qual/version1"
_SIGN_MAP = {"positive": "activation", "negative": "inhibition", "unknown": "activation"}


def _local(tag: str) -> str:
    return tag.split("}")[-1] if "}" in tag else tag


def _attr(el: ET.Element, local: str) -> str | None:
    for key, val in el.attrib.items():
        if _local(key) == local:
            return val
    return None


def parse_sbml(source: str | Path) -> Graph:
    """Parse an SBML Level 3 / qual file and return a :class:`~biopulse.model.graph.Graph`.

    Only the qualitative species and transitions are read; kinetic rate laws
    and SBML core model elements are ignored.

    Args:
        source: File path or ``pathlib.Path`` to an ``.sbml`` or ``.xml`` file.

    Returns:
        A :class:`~biopulse.model.graph.Graph` with nodes derived from
        ``qualitativeSpecies`` and edges derived from ``transition`` inputs →
        outputs.

    Raises:
        ValueError: If no qualitative species or transitions are found, or if
            an input's sign is unrecognised.
    """
    tree = ET.parse(str(source))
    root = tree.getroot()

    # Walk all elements, matching by local name (namespace-agnostic)
    def _iter_local(parent: ET.Element, local_name: str) -> list[ET.Element]:
        return [el for el in parent.iter() if _local(el.tag) == local_name]

    # ── Nodes from qualitativeSpecies ────────────────────────────────────────
    node_dicts: list[dict[str, str]] = []
    seen_nodes: set[str] = set()

    for qs in _iter_local(root, "qualitativeSpecies"):
        nid = _attr(qs, "id")
        if not nid or nid in seen_nodes:
            continue
        seen_nodes.add(nid)
        entry: dict[str, str] = {"id": nid}
        compartment = _attr(qs, "compartment")
        if compartment:
            entry["group"] = compartment
        node_dicts.append(entry)

    # ── Edges from transitions ───────────────────────────────────────────────
    edge_dicts: list[dict[str, str]] = []
    seen_edges: set[tuple[str, str]] = set()

    for transition in _iter_local(root, "transition"):
        inputs: list[tuple[str, str]] = []  # (species_id, edge_type)
        for inp in _iter_local(transition, "input"):
            sp = _attr(inp, "qualitativeSpecies")
            if not sp:
                continue
            raw_sign = _attr(inp, "sign") or "positive"
            etype = _SIGN_MAP.get(raw_sign)
            if etype is None:
                raise ValueError(
                    f"Unknown SBML qual input sign {raw_sign!r}; "
                    "expected 'positive', 'negative', or 'unknown'."
                )
            inputs.append((sp, etype))

        outputs: list[str] = []
        for out in _iter_local(transition, "output"):
            sp = _attr(out, "qualitativeSpecies")
            if sp:
                outputs.append(sp)

        for src, etype in inputs:
            for tgt in outputs:
                key = (src, tgt)
                if key not in seen_edges:
                    edge_dicts.append({"source": src, "target": tgt, "type": etype})
                    seen_edges.add(key)

    schema = GraphSchema.model_validate({"nodes": node_dicts, "edges": edge_dicts})
    return Graph(schema)
