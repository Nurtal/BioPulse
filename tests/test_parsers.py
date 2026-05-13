"""Tests for Phase 5 biological parsers: SIF, GINML, SBML-qual."""

from __future__ import annotations

import io
import textwrap
from pathlib import Path

import pytest

import biopulse
from biopulse.model.graph import Graph
from biopulse.parsers.ginml import parse_ginml
from biopulse.parsers.sbml import parse_sbml
from biopulse.parsers.sif import parse_sif

EXAMPLES = Path(__file__).parent.parent / "examples" / "data"


# ===========================================================================
# SIF parser
# ===========================================================================


class TestSifParser:
    # ── happy-path ──────────────────────────────────────────────────────────

    def test_returns_graph(self) -> None:
        sif = "A 1 B\n"
        assert isinstance(parse_sif(io.StringIO(sif)), Graph)

    def test_public_api_alias(self) -> None:
        assert biopulse.parse_sif is parse_sif

    def test_activation_from_1(self) -> None:
        g = parse_sif(io.StringIO("A 1 B\n"))
        edges = g.schema.edges
        assert len(edges) == 1
        assert edges[0].type == "activation"

    def test_inhibition_from_minus1(self) -> None:
        g = parse_sif(io.StringIO("A -1 B\n"))
        assert g.schema.edges[0].type == "inhibition"

    def test_activation_aliases(self) -> None:
        for tok in ["a", "+", "activates", "activate", "activation", "->"]:
            g = parse_sif(io.StringIO(f"A {tok} B\n"))
            assert g.schema.edges[0].type == "activation", tok

    def test_inhibition_aliases(self) -> None:
        for tok in ["i", "-", "inhibits", "inhibit", "inhibition", "-|"]:
            g = parse_sif(io.StringIO(f"A {tok} B\n"))
            assert g.schema.edges[0].type == "inhibition", tok

    def test_type_matching_case_insensitive(self) -> None:
        g = parse_sif(io.StringIO("A ACTIVATES B\n"))
        assert g.schema.edges[0].type == "activation"

    def test_multiple_targets_on_one_line(self) -> None:
        g = parse_sif(io.StringIO("A 1 B C D\n"))
        assert {e.target for e in g.schema.edges} == {"B", "C", "D"}
        assert all(e.type == "activation" for e in g.schema.edges)

    def test_nodes_deduplicated(self) -> None:
        sif = "A 1 B\nA -1 C\n"
        g = parse_sif(io.StringIO(sif))
        assert len(g.schema.nodes) == 3

    def test_edges_deduplicated(self) -> None:
        sif = "A 1 B\nA 1 B\n"
        g = parse_sif(io.StringIO(sif))
        assert len(g.schema.edges) == 1

    def test_comments_and_blank_lines_ignored(self) -> None:
        sif = textwrap.dedent("""\
            # header comment
            A 1 B

            # another comment
            B -1 A
        """)
        g = parse_sif(io.StringIO(sif))
        assert len(g.schema.nodes) == 2
        assert len(g.schema.edges) == 2

    def test_tab_separated(self) -> None:
        g = parse_sif(io.StringIO("A\t1\tB\n"))
        assert len(g.schema.edges) == 1

    def test_from_path(self) -> None:
        g = parse_sif(EXAMPLES / "toggle_switch.sif")
        assert {n.id for n in g.schema.nodes} == {"A", "B"}
        assert len(g.schema.edges) == 2
        assert all(e.type == "inhibition" for e in g.schema.edges)

    def test_il6_stat3_sif(self) -> None:
        g = parse_sif(EXAMPLES / "il6_stat3.sif")
        assert {n.id for n in g.schema.nodes} == {"IL6", "JAK1", "STAT3", "SOCS3"}
        types = {(e.source, e.target): e.type for e in g.schema.edges}
        assert types[("IL6", "JAK1")] == "activation"
        assert types[("SOCS3", "JAK1")] == "inhibition"

    def test_default_type_for_unknown(self) -> None:
        g = parse_sif(io.StringIO("A pp B\n"), default_type="activation")
        assert g.schema.edges[0].type == "activation"

    # ── error cases ─────────────────────────────────────────────────────────

    def test_unknown_type_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown SIF interaction type"):
            parse_sif(io.StringIO("A pp B\n"))

    def test_too_few_columns_raises(self) -> None:
        with pytest.raises(ValueError, match="3 columns"):
            parse_sif(io.StringIO("A 1\n"))

    def test_invalid_default_type_raises(self) -> None:
        with pytest.raises(ValueError, match="default_type must be"):
            parse_sif(io.StringIO("A 1 B\n"), default_type="unknown")


# ===========================================================================
# GINML parser
# ===========================================================================


class TestGinmlParser:
    _SIMPLE = textwrap.dedent("""\
        <?xml version="1.0" encoding="UTF-8"?>
        <GINsim-model id="test">
          <nodelist>
            <node id="A" maxvalue="1"/>
            <node id="B" maxvalue="1"/>
          </nodelist>
          <edgelist>
            <edge from="A" to="B" minvalue="1" sign="positive"/>
            <edge from="B" to="A" minvalue="1" sign="negative"/>
          </edgelist>
        </GINsim-model>
    """)

    def _parse(self, xml: str) -> Graph:
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".ginml", delete=False) as f:
            f.write(xml)
            name = f.name
        try:
            return parse_ginml(name)
        finally:
            os.unlink(name)

    def test_returns_graph(self) -> None:
        assert isinstance(self._parse(self._SIMPLE), Graph)

    def test_public_api_alias(self) -> None:
        assert biopulse.parse_ginml is parse_ginml

    def test_nodes_parsed(self) -> None:
        g = self._parse(self._SIMPLE)
        assert {n.id for n in g.schema.nodes} == {"A", "B"}

    def test_positive_sign_is_activation(self) -> None:
        g = self._parse(self._SIMPLE)
        a_to_b = next(e for e in g.schema.edges if e.source == "A" and e.target == "B")
        assert a_to_b.type == "activation"

    def test_negative_sign_is_inhibition(self) -> None:
        g = self._parse(self._SIMPLE)
        b_to_a = next(e for e in g.schema.edges if e.source == "B" and e.target == "A")
        assert b_to_a.type == "inhibition"

    def test_missing_sign_defaults_to_activation(self) -> None:
        xml = textwrap.dedent("""\
            <?xml version="1.0"?>
            <GINsim-model id="x">
              <nodelist><node id="A"/><node id="B"/></nodelist>
              <edgelist><edge from="A" to="B" minvalue="1"/></edgelist>
            </GINsim-model>
        """)
        g = self._parse(xml)
        assert g.schema.edges[0].type == "activation"

    def test_nodeclass_becomes_group(self) -> None:
        xml = textwrap.dedent("""\
            <?xml version="1.0"?>
            <GINsim-model id="x">
              <nodelist><node id="A" nodeclass="kinase"/></nodelist>
              <edgelist/>
            </GINsim-model>
        """)
        g = self._parse(xml)
        assert g.schema.nodes[0].group == "kinase"

    def test_example_file(self) -> None:
        g = parse_ginml(EXAMPLES / "toggle_switch.ginml")
        assert {n.id for n in g.schema.nodes} == {"A", "B"}
        assert len(g.schema.edges) == 2
        groups = {n.id: n.group for n in g.schema.nodes}
        assert groups["A"] == "activator"
        assert groups["B"] == "repressor"

    def test_wrong_root_raises(self) -> None:
        xml = "<sbml/>"
        with pytest.raises(ValueError, match="GINsim"):
            self._parse(xml)

    def test_unknown_sign_raises(self) -> None:
        xml = textwrap.dedent("""\
            <?xml version="1.0"?>
            <GINsim-model id="x">
              <nodelist><node id="A"/><node id="B"/></nodelist>
              <edgelist><edge from="A" to="B" sign="neutral"/></edgelist>
            </GINsim-model>
        """)
        with pytest.raises(ValueError, match="Unknown GINML edge sign"):
            self._parse(xml)


# ===========================================================================
# SBML-qual parser
# ===========================================================================


class TestSbmlParser:
    def test_returns_graph(self) -> None:
        assert isinstance(parse_sbml(EXAMPLES / "il6_stat3.sbml"), Graph)

    def test_public_api_alias(self) -> None:
        assert biopulse.parse_sbml is parse_sbml

    def test_nodes_from_qualitative_species(self) -> None:
        g = parse_sbml(EXAMPLES / "il6_stat3.sbml")
        assert {n.id for n in g.schema.nodes} == {"IL6", "JAK1", "STAT3", "SOCS3"}

    def test_compartment_becomes_group(self) -> None:
        g = parse_sbml(EXAMPLES / "il6_stat3.sbml")
        groups = {n.id: n.group for n in g.schema.nodes}
        assert groups["IL6"] == "extracellular"
        assert groups["JAK1"] == "cytoplasm"
        assert groups["STAT3"] == "nucleus"

    def test_positive_sign_is_activation(self) -> None:
        g = parse_sbml(EXAMPLES / "il6_stat3.sbml")
        types = {(e.source, e.target): e.type for e in g.schema.edges}
        assert types[("IL6", "JAK1")] == "activation"
        assert types[("JAK1", "STAT3")] == "activation"

    def test_negative_sign_is_inhibition(self) -> None:
        g = parse_sbml(EXAMPLES / "il6_stat3.sbml")
        types = {(e.source, e.target): e.type for e in g.schema.edges}
        assert types[("SOCS3", "JAK1")] == "inhibition"

    def test_edges_count(self) -> None:
        g = parse_sbml(EXAMPLES / "il6_stat3.sbml")
        # IL6→JAK1, SOCS3→JAK1, JAK1→STAT3, STAT3→SOCS3
        assert len(g.schema.edges) == 4

    def test_edges_deduplicated(self) -> None:
        import os
        import tempfile

        xml = textwrap.dedent("""\
            <?xml version="1.0"?>
            <sbml xmlns:qual="http://www.sbml.org/sbml/level3/version1/qual/version1">
              <model>
                <qual:listOfQualitativeSpecies>
                  <qual:qualitativeSpecies qual:id="A"/>
                  <qual:qualitativeSpecies qual:id="B"/>
                </qual:listOfQualitativeSpecies>
                <qual:listOfTransitions>
                  <qual:transition>
                    <qual:listOfInputs>
                      <qual:input qual:qualitativeSpecies="A" qual:sign="positive"/>
                      <qual:input qual:qualitativeSpecies="A" qual:sign="positive"/>
                    </qual:listOfInputs>
                    <qual:listOfOutputs>
                      <qual:output qual:qualitativeSpecies="B"/>
                    </qual:listOfOutputs>
                  </qual:transition>
                </qual:listOfTransitions>
              </model>
            </sbml>
        """)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sbml", delete=False) as f:
            f.write(xml)
            name = f.name
        try:
            g = parse_sbml(name)
        finally:
            os.unlink(name)
        assert len(g.schema.edges) == 1

    def test_unknown_sign_raises(self) -> None:
        import os
        import tempfile

        xml = textwrap.dedent("""\
            <?xml version="1.0"?>
            <sbml xmlns:qual="http://www.sbml.org/sbml/level3/version1/qual/version1">
              <model>
                <qual:listOfQualitativeSpecies>
                  <qual:qualitativeSpecies qual:id="A"/>
                  <qual:qualitativeSpecies qual:id="B"/>
                </qual:listOfQualitativeSpecies>
                <qual:listOfTransitions>
                  <qual:transition>
                    <qual:listOfInputs>
                      <qual:input qual:qualitativeSpecies="A" qual:sign="dual"/>
                    </qual:listOfInputs>
                    <qual:listOfOutputs>
                      <qual:output qual:qualitativeSpecies="B"/>
                    </qual:listOfOutputs>
                  </qual:transition>
                </qual:listOfTransitions>
              </model>
            </sbml>
        """)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sbml", delete=False) as f:
            f.write(xml)
            name = f.name
        try:
            with pytest.raises(ValueError, match="Unknown SBML qual input sign"):
                parse_sbml(name)
        finally:
            os.unlink(name)
