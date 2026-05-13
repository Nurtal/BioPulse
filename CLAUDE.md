# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Current state

This repo is **pre-code**. Only `README.md` and `ROADMAP.md` exist — no `pyproject.toml`, no source tree, no tests, no CI. Any "build/lint/test" command must be created as part of Phase 0 before it can be invoked. Do not invent commands that do not exist; if asked to run tests or lint, the first task is to scaffold the project per `ROADMAP.md` Phase 0.

The intended package layout is documented in `README.md` (the `biopulse/` tree under "Architecture"). Follow that structure when creating files.

## Architectural invariants

These come from `README.md` "Core Principles" and constrain every design decision:

1. **Renderer-first, not a simulator.** BioPulse renders pre-computed dynamics; it does not compute Boolean trajectories. Simulation engines (PyBoolNet, MPBN, etc.) are *upstream* and feed BioPulse via the canonical format. Do not add simulation logic into `core/` or `model/`.

2. **Canonical internal JSON is the only data contract.** All parsers (`parsers/sif.py`, `parsers/sbml.py`, `parsers/ginml.py`) convert *into* the schema in `model/schema.py`. The renderer reads *only* the canonical form. Never let a parser-specific structure leak past `parsers/`.

3. **Event-driven, not snapshot-driven.** State over time is expressed as a stream of `{t, node, state}` events (see "Internal JSON Format" in `README.md`), not as per-frame node-state dumps. Interpolation between events is the renderer's job. If you find yourself materializing per-frame snapshots in the data layer, you're on the wrong track.

## Open decisions that block implementation

`ROADMAP.md` flags these as "Décisions critiques à prendre tôt". They are **not yet decided** — do not silently pick one. Surface the choice to the user before writing code that depends on it:

- **Rendering backend** — Pyglet/moderngl vs PixiJS-via-anywidget vs Matplotlib vs Three.js/pythreejs. Cascades into the entire `core/renderer/` design, notebook-vs-desktop UX, and export pipeline. Trade-offs are tabulated at the bottom of `ROADMAP.md`.
- **2D vs 3D coordinates** — start 2D per roadmap.
- **Notebook-first vs standalone app** — roadmap recommends notebook-first.

## Phase ordering

`ROADMAP.md` is the source of truth for what gets built when. Key gates:

- Phase 0 (scaffolding) must produce a working `pip install -e .` before any feature work.
- Phase 1 (model + JSON I/O) must land before Phase 2 (rendering) — the renderer consumes the canonical schema, so the schema is the upstream dependency.
- **MVP = end of Phase 3** (`biopulse.play(graph, events)` animating a cascade end-to-end). Don't pull Phase 4+ features (interaction, parsers, exporters, shaders) into earlier phases without explicit user agreement.

Pydantic v2 is the chosen validation library (per roadmap decision table).
