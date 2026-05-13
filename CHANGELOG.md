# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Phase 7 advanced visual effects:
  - **Glow** (`glow_enabled`) — soft bloom halo around active/highlighted nodes; drawn as GLOW_LAYERS concentric semi-transparent circles below the node. On by default for `PlayWidget`, off for `GraphWidget` (only activates when `highlighted_nodes` is non-empty).
  - **Pulse rings** (`pulse_ring_enabled`) — expanding, fading ring emitted from a node the moment it activates; ring grows to 3.5× node radius over `RING_DUR=0.55s`. Seek-safe: derived from `nodeStates[id].tChanged`.
  - **Heatmap** (`heatmap_enabled`) — node colour reflects cumulative activation count; cold (dark blue `#2D5986`) → hot (amber `#FF9A00`) using the new `heatmap_color()` utility. Activation counts are rebuilt from scratch on seek.
  - **Particles** (`particles_enabled`) — 3 particles per outgoing activation edge fired when a source activates; particles travel from source to target over `PARTICLE_DUR=0.7s` with fade-in/fade-out alpha.
  - **Tooltip enhancement** — shows "Activations: N" when the heatmap count is known.
  - Python interp utilities: `ring_progress`, `ring_alpha`, `ring_radius`, `heatmap_color` added to `biopulse.core.animation.interp`.
  - New traitlets: `GraphWidget.glow_enabled`; `PlayWidget.glow_enabled`, `pulse_ring_enabled`, `heatmap_enabled`, `particles_enabled`.
  - 33 new tests in `tests/test_phase7.py`.

- Phase 6 export utilities (`biopulse.io.exporters`):
  - `export_graph(graph, path)` — serialize a `Graph` to canonical JSON; round-trippable via `load_graph`.
  - `export_events(events, path)` — serialize an `EventStream` to `{"events": [...]}` JSON; round-trippable via `load_events`.
  - `export_scene(graph, events, path)` — serialize graph + events to scene JSON; round-trippable via `load_scene`.
  - `export_html(graph, path, *, events=None, ...)` — write a self-contained HTML file that opens in any browser without Jupyter or Python. Static mode (no events) renders a fully interactive graph (zoom/pan, tooltip, click-to-highlight). Animated mode (with events) adds the HTML control bar (restart/play-pause/speed/scrubber). PixiJS loaded from CDN; a thin anywidget model shim makes the existing renderer JS work unchanged.
  - All four functions exposed on the `biopulse` top-level namespace.
  - 36 new tests in `tests/test_exporters.py` covering round-trips, cross-validation, HTML structure, and embedded data.

- Phase 5 biological parsers:
  - `biopulse.parsers.sif` — SIF (Simple Interaction Format) parser: whitespace/tab-separated, multi-target lines, `#` comments, 10+ interaction-type aliases (`1`, `-1`, `activates`, `inhibits`, `->`, `-|`, …), configurable `default_type` fallback.
  - `biopulse.parsers.ginml` — GINML (GINsim native XML) parser: reads `<node>` / `<edge>` elements, maps `sign="positive/negative"` → activation/inhibition, extracts `nodeclass` → `group`.
  - `biopulse.parsers.sbml` — SBML Level 3 + qual parser (stdlib `xml.etree.ElementTree`, no `python-libsbml` required): reads `qualitativeSpecies` as nodes (with `compartment` → `group`), derives edges from `transition` input→output pairs with `sign` attribute.
  - All three parsers exposed on the top-level `biopulse` namespace: `parse_sif`, `parse_ginml`, `parse_sbml`.
  - Example data files: `examples/data/toggle_switch.sif`, `il6_stat3.sif`, `toggle_switch.ginml`, `il6_stat3.sbml`.
  - 37 new tests in `tests/test_parsers.py` covering happy paths, alias handling, deduplication, group extraction, and error cases.

- Phase 4 user interactions:
  - **Zoom / pan** — scroll-to-zoom toward cursor + drag-to-pan via a world `PIXI.Container`; both `GraphWidget` and `PlayWidget` renderers.
  - **Node hover tooltip** — absolute-positioned HTML overlay showing node id, group (if set), and (in `PlayWidget`) current animation state (active/inactive).
  - **Click-to-highlight** — BFS upstream + downstream path from the clicked node; non-path nodes and edges dim to alpha 0.12; click the same node again to clear. Pan + click is disambiguated by a `hasMoved` flag.
  - **`highlighted_nodes` traitlet** — Python can drive highlights programmatically on both `GraphWidget` and `PlayWidget`; client-side listener merges Python-driven and click-driven highlight sets.
  - **`group` field** in `build_graph_data` — node entries now include `group` when present in the schema, consumed by tooltips.
  - **HTML control bar** (`PlayWidget` only) — restart (⏮), play/pause toggle, speed buttons (0.5×/1×/2×/4× with `.bp-active` state), timeline scrubber (`<input type=range>`), and a live time label; styled by `_CONTROLS_CSS`.
  - 16 new Python tests in `tests/test_phase4.py` covering highlighted_nodes traitlets, group field in graph data, and CSS controls.

- Phase 0 scaffolding: `pyproject.toml` (hatchling), package tree per README architecture, smoke test, MIT license, CI on Python 3.11/3.12, ruff/mypy/pytest config.
- Phase 3 animated playback — **MVP reached** ✅:
  - `Clock` — pure play/pause/stop/seek/tick state machine (`biopulse.core.timeline.clock`)
  - `Scheduler` — `events_in_window` for ticker loop, `active_events_at` for seek (`biopulse.core.timeline.scheduler`)
  - `AnimationState` — per-node visual state tracking with prev/current active flags (`biopulse.core.animation.state`)
  - `ease_in_out`, `lerp`, `lerp_color`, `pulse_scale` interpolation utilities (`biopulse.core.animation.interp`)
  - `_pixi_play.js` — PixiJS v7 60 fps ticker; colour fade + scale pulse on activation/deactivation; seek support via `current_t` traitlet
  - `PlayWidget` — anywidget class with `events_data`, `playback_state`, `playback_speed`, `current_t`, `duration` traitlets
  - Public API: `biopulse.play(graph, events, *, layout, width, height, show_labels, speed, autoplay) -> PlayWidget`
  - End-to-end example: `examples/play_cascade.py` (Jupyter usage of IL-6/STAT3 cascade)
- Phase 2 static renderer (anywidget + PixiJS v7):
  - `Layout` protocol and `ForceAtlasLayout` (NetworkX spring_layout wrapper) (`biopulse.layouts`)
  - `GraphWidget` anywidget class with PixiJS ESM renderer: nodes as circles, directed edges with arrowheads (activation) or flat bars (inhibition), colour-coded (`biopulse.core.renderer`)
  - `_positions_to_pixels` coordinate mapper and `build_graph_data` serialiser
  - Public API: `biopulse.show(graph, *, layout, width, height, show_labels) -> GraphWidget`
  - Visual snapshot tests are deferred (require browser); Python-layer tests cover layout, coordinate mapping, widget instantiation, and `show()` wiring
- Phase 1 data model and JSON I/O:
  - Pydantic v2 schemas: `Node`, `Edge`, `Graph`, `Event`, `EventStream` (wire envelope), `Scene` with cross-validation (`biopulse.model.schema`)
  - Operational `EventStream` with sort-on-load and bisect-based seek: `at_or_before`, `after`, `between` (`biopulse.model.events`)
  - `Graph` wrapper around `networkx.DiGraph` preserving node/edge attributes (`biopulse.model.graph`)
  - JSON loaders: `load_graph`, `load_events`, `load_scene` (`biopulse.io.json_loader`)
  - Exported JSON Schemas in `schema/` (graph, event, scene)
  - Example data files in `examples/data/` (IL6→STAT3 scene, feedforward loop graph, toggle events)
