"""
BioPulse — animation export example
====================================

This script builds a small IL-6 / STAT3 signalling cascade from scratch,
animates a sequential activation + negative-feedback cycle, and exports it
as a GIF and as a standalone HTML file.

Run from the repo root:
    python examples/export_animation.py

Requirements:
    pip install 'biopulse[export]'   # for GIF/MP4
"""

from pathlib import Path

import biopulse
from biopulse.model.events import EventStream
from biopulse.model.graph import Graph
from biopulse.model.schema import Event
from biopulse.model.schema import Graph as GraphSchema

OUT = Path(__file__).parent / "data"
OUT.mkdir(exist_ok=True)

# ── Build the graph ────────────────────────────────────────────────────────────

nodes = [
    {"id": "IL6", "group": "cytokine"},
    {"id": "JAK1", "group": "kinase"},
    {"id": "STAT3", "group": "transcription_factor"},
    {"id": "MYC", "group": "target_gene"},
    {"id": "BCL2", "group": "target_gene"},
    {"id": "SOCS3", "group": "feedback"},
]
edges = [
    {"source": "IL6", "target": "JAK1", "type": "activation"},
    {"source": "JAK1", "target": "STAT3", "type": "activation"},
    {"source": "STAT3", "target": "MYC", "type": "activation"},
    {"source": "STAT3", "target": "BCL2", "type": "activation"},
    {"source": "STAT3", "target": "SOCS3", "type": "activation"},
    {"source": "SOCS3", "target": "JAK1", "type": "inhibition"},
]
graph = Graph(GraphSchema.model_validate({"nodes": nodes, "edges": edges}))

# ── Define the event timeline ──────────────────────────────────────────────────
#
# t=0.0  IL6 ligand arrives
# t=0.4  JAK1 kinase activates
# t=0.9  STAT3 translocates to nucleus
# t=1.3  MYC and BCL2 target genes switch on
# t=1.7  SOCS3 feedback inhibitor expressed
# t=2.2  JAK1 inhibited by SOCS3 → turns off
# t=2.6  STAT3 loses JAK1 signal → turns off
# t=3.0  target genes deactivated

events = EventStream(
    [
        Event(t=0.0, node="IL6", state=1),
        Event(t=0.4, node="JAK1", state=1),
        Event(t=0.9, node="STAT3", state=1),
        Event(t=1.3, node="MYC", state=1),
        Event(t=1.3, node="BCL2", state=1),
        Event(t=1.7, node="SOCS3", state=1),
        Event(t=2.2, node="JAK1", state=0),
        Event(t=2.6, node="STAT3", state=0),
        Event(t=3.0, node="MYC", state=0),
        Event(t=3.0, node="BCL2", state=0),
    ]
)

# ── Export GIF ─────────────────────────────────────────────────────────────────

gif_path = OUT / "il6_stat3_cascade.gif"
biopulse.export_gif(
    graph,
    events,
    gif_path,
    width=500,
    height=380,
    fps=20,
    speed=0.8,
)
print(f"GIF  → {gif_path}  ({gif_path.stat().st_size // 1024} KB)")

# ── Export standalone HTML ─────────────────────────────────────────────────────

html_path = OUT / "il6_stat3_cascade.html"
biopulse.export_html(
    graph,
    html_path,
    events=events,
    width=700,
    height=500,
    title="IL-6 / STAT3 Signalling Cascade",
)
print(f"HTML → {html_path}  ({html_path.stat().st_size // 1024} KB)")

# ── Export canonical JSON (round-trip) ─────────────────────────────────────────

scene_path = OUT / "il6_stat3_cascade.scene.json"
biopulse.export_scene(graph, events, scene_path)
print(f"JSON → {scene_path}")

print("\nDone!  Open the HTML file in any browser for the interactive version.")
