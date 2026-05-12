# BioPulse

**BioPulse** is a Python package for the dynamic visualization of Boolean and biological networks.

It aims to provide a modern, animated, GPU-friendly rendering engine for:

* Boolean regulatory networks
* Signaling pathways
* Disease maps
* Cell-cell communication systems
* Dynamical biological simulations

BioPulse focuses on **visual storytelling of biological dynamics**, inspired by tools such as Gource, modern game engines, and systems biology simulators.

---

# Vision

Most biological network visualization tools are:

* static,
* difficult to explore dynamically,
* designed for analysis rather than visual understanding.

BioPulse aims to bridge the gap between:

* systems biology,
* network science,
* real-time rendering,
* scientific communication.

The long-term goal is to make biological systems feel **alive**.

---

# Core Principles

## 1. Renderer-first architecture

BioPulse is primarily a **visualization engine**, not a simulation framework.

Simulation engines should export data into a common internal format which BioPulse can render efficiently.

---

## 2. JSON canonical format

Internally, BioPulse uses a unified JSON schema for:

* graph structures,
* node states,
* temporal events,
* animations.

All external formats are converted into this internal representation.

---

## 3. Event-driven animation

Instead of storing only snapshots of network states, BioPulse uses event streams:

```json
{
  "t": 1.24,
  "node": "STAT3",
  "state": 1
}
```

This enables:

* smooth interpolation,
* cinematic animations,
* real-time playback,
* GPU acceleration,
* video export.

---

# Planned Features

## Graph Rendering

* GPU-accelerated rendering
* Large graph support
* Force-directed layouts
* Biological hierarchical layouts
* Pathway grouping
* Edge bundling

---

## Dynamic Animation

* Node activation pulses
* Inhibition effects
* Signal propagation
* Temporal interpolation
* Activity heatmaps
* Attractor visualization

---

## Biological Network Support

* SIF import
* SBML-qual import
* GINML import
* Boolean network support
* Signed directed graphs

---

## Interaction

* Zoom/pan
* Timeline scrubbing
* Pause/replay
* Node inspection
* Path highlighting
* Interactive filtering

---

## Export

* MP4/GIF rendering
* Interactive HTML export
* Frame-by-frame export
* JSON serialization

---

# Initial Scope (MVP)

The first version of BioPulse will focus only on:

* Loading a graph from JSON
* Rendering animated node activations
* Simple force-directed layout
* Temporal playback
* Event-based animation

No biological logic engine will initially be implemented.

The renderer will only consume:

* graph structure,
* event timelines.

---

# Architecture

```text
biopulse/
│
├── core/
│   ├── renderer/
│   ├── animation/
│   ├── shaders/
│   └── timeline/
│
├── model/
│   ├── graph.py
│   ├── events.py
│   └── schema.py
│
├── parsers/
│   ├── sif.py
│   ├── sbml.py
│   └── ginml.py
│
├── layouts/
│   ├── forceatlas.py
│   └── hierarchical.py
│
├── io/
│   ├── json_loader.py
│   └── exporters.py
│
└── examples/
```

---

# Internal JSON Format (Draft)

## Graph Structure

```json
{
  "nodes": [
    {
      "id": "STAT3",
      "group": "JAK_STAT"
    }
  ],
  "edges": [
    {
      "source": "IL6",
      "target": "STAT3",
      "type": "activation"
    }
  ]
}
```

---

## Simulation Events

```json
{
  "events": [
    {
      "t": 0.12,
      "node": "IL6",
      "state": 1
    },
    {
      "t": 0.42,
      "node": "STAT3",
      "state": 1
    }
  ]
}
```

---

# Technology Stack

## Core Language

Python

---

## Rendering Backend (planned)

* WebGL / WebGPU
* PixiJS
* Three.js (optional)

---

## Graph Processing

* NetworkX
* Graphology interoperability

---

## Future Goals

* WebAssembly support
* Cytoscape interoperability
* Live simulation streaming
* Multi-layer biological networks
* Spatial reaction-diffusion rendering
* Immune system visual dynamics

---

# Development Roadmap

## Phase 1 — Minimal Renderer

* [ ] JSON schema
* [ ] Basic graph rendering
* [ ] Timeline engine
* [ ] Event playback
* [ ] Force layout

---

## Phase 2 — Biological Features

* [ ] SIF parser
* [ ] Signed edges
* [ ] Pathway grouping
* [ ] Node metadata

---

## Phase 3 — Advanced Animation

* [ ] GPU shaders
* [ ] Signal propagation effects
* [ ] Glow / bloom
* [ ] Edge particles
* [ ] Attractor transitions

---

## Phase 4 — Ecosystem Integration

* [ ] SBML-qual support
* [ ] GINML support
* [ ] PyBoolNet interoperability
* [ ] MPBN interoperability

---

# Example Future Use Cases

* Visualizing inflammation propagation
* Comparing disease attractors
* Showing treatment perturbations
* Educational systems biology demos
* Animated supplementary figures for publications
* Interactive conference presentations

---

# Philosophy

BioPulse is not meant to replace analysis tools.

It is meant to make complex biological systems:

* intuitive,
* dynamic,
* explorable,
* visually expressive.

---

# License

MIT License

---

# Status

Early-stage experimental project.

