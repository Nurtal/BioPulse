/**
 * BioPulse animated graph renderer — PixiJS v7.
 *
 * Phase 4 interactions:
 *   - Scroll to zoom, drag to pan (world container)
 *   - Hover node → HTML tooltip (id, group, active state)
 *   - Click node → BFS upstream + downstream path highlight; click again to clear
 *   - highlighted_nodes traitlet: Python can drive highlights programmatically
 *   - HTML control bar: restart | play/pause | speed (0.5×/1×/2×/4×) | scrubber | time
 *
 * Phase 7 visual effects (all togglable via traitlets):
 *   - glow_enabled       Soft bloom halo around active nodes
 *   - pulse_ring_enabled  Expanding ring emitted on each activation
 *   - heatmap_enabled    Node colour tracks cumulative activation count (amber = hot)
 *   - particles_enabled  Particles travel along outgoing activation edges on fire
 *
 * Traitlets (synced with Python):
 *   graph_data, events_data, playback_state, playback_speed, current_t, duration,
 *   show_labels, highlighted_nodes, width, height,
 *   glow_enabled, pulse_ring_enabled, heatmap_enabled, particles_enabled
 */

import * as PIXI from "https://esm.sh/pixi.js@7";

const NODE_RADIUS    = 12;
const INACTIVE_COLOR = 0x2d5986;
const ACTIVE_COLOR   = 0x4fc3f7;
const HEAT_COLOR     = 0xff9a00;
const GLOW_COLOR     = 0x4fc3f7;
const EDGE_COLORS    = { activation: 0x7ec8e3, inhibition: 0xff6b6b };
const BG_COLOR       = 0x1a1a2e;
const FADE_DUR       = 0.35;
const PULSE_DUR      = 0.45;
const RING_DUR       = 0.55;
const PARTICLE_DUR   = 0.7;
const GLOW_LAYERS    = 4;
const DIM_ALPHA      = 0.12;

// ── Colour helpers ────────────────────────────────────────────────────────────

function easeInOut(t) {
  t = Math.max(0, Math.min(1, t));
  return t * t * (3 - 2 * t);
}

function lerpColor(c1, c2, t) {
  const ch = (c, s) => (c >> s) & 0xff;
  return (Math.round(ch(c1, 16) + (ch(c2, 16) - ch(c1, 16)) * t) << 16)
       | (Math.round(ch(c1,  8) + (ch(c2,  8) - ch(c1,  8)) * t) <<  8)
       |  Math.round(ch(c1,  0) + (ch(c2,  0) - ch(c1,  0)) * t);
}

// ── Edge drawing helpers ──────────────────────────────────────────────────────

function drawArrow(gfx, x1, y1, x2, y2, color, alpha = 0.85) {
  const dx = x2 - x1, dy = y2 - y1;
  const len = Math.sqrt(dx * dx + dy * dy) || 1;
  const ux = dx / len, uy = dy / len;
  const ex = x2 - ux * NODE_RADIUS, ey = y2 - uy * NODE_RADIUS;
  const sz = 8;
  gfx.lineStyle(1.5, color, alpha);
  gfx.moveTo(x1 + ux * NODE_RADIUS, y1 + uy * NODE_RADIUS);
  gfx.lineTo(ex, ey);
  gfx.beginFill(color, alpha);
  gfx.drawPolygon([
    ex, ey,
    ex - ux * sz - uy * sz / 2, ey - uy * sz + ux * sz / 2,
    ex - ux * sz + uy * sz / 2, ey - uy * sz - ux * sz / 2,
  ]);
  gfx.endFill();
}

function drawBar(gfx, x1, y1, x2, y2, color, alpha = 0.85) {
  const dx = x2 - x1, dy = y2 - y1;
  const len = Math.sqrt(dx * dx + dy * dy) || 1;
  const ux = dx / len, uy = dy / len;
  const bx = x2 - ux * NODE_RADIUS, by = y2 - uy * NODE_RADIUS;
  gfx.lineStyle(1.5, color, alpha);
  gfx.moveTo(x1 + ux * NODE_RADIUS, y1 + uy * NODE_RADIUS);
  gfx.lineTo(bx, by);
  gfx.lineStyle(2.5, color, alpha);
  gfx.moveTo(bx - uy * 8, by + ux * 8);
  gfx.lineTo(bx + uy * 8, by - ux * 8);
}

// ── BFS path computation ──────────────────────────────────────────────────────

function computePathNodes(nodeId, edges) {
  const result = new Set([nodeId]);
  let frontier = [nodeId];
  while (frontier.length) {
    const next = [];
    for (const n of frontier) {
      for (const e of edges) {
        if (e.source === n && !result.has(e.target)) { result.add(e.target); next.push(e.target); }
        if (e.target === n && !result.has(e.source)) { result.add(e.source); next.push(e.source); }
      }
    }
    frontier = next;
  }
  return result;
}

// ── Main render ───────────────────────────────────────────────────────────────

export function render({ model, el }) {
  const width  = model.get("width");
  const height = model.get("height");

  el.style.position = "relative";

  const app = new PIXI.Application({
    width, height, backgroundColor: BG_COLOR, antialias: true,
    resolution: (typeof window !== "undefined" && window.devicePixelRatio) || 1,
    autoDensity: true,
  });
  el.appendChild(app.view);

  // World container — zoom/pan target; layer order bottom → top
  const world      = new PIXI.Container();
  const glowLayer  = new PIXI.Graphics();
  const edgeLayer  = new PIXI.Graphics();
  const ringLayer  = new PIXI.Graphics();
  const nodeLayer  = new PIXI.Container();
  const labelLayer = new PIXI.Container();
  const partLayer  = new PIXI.Graphics();
  app.stage.addChild(world);
  world.addChild(glowLayer);
  world.addChild(edgeLayer);
  world.addChild(ringLayer);
  world.addChild(nodeLayer);
  world.addChild(labelLayer);
  world.addChild(partLayer);

  // HTML tooltip
  const tooltip = document.createElement("div");
  Object.assign(tooltip.style, {
    position: "absolute", background: "#0d1117",
    border: "1px solid #4fc3f7", borderRadius: "5px",
    padding: "5px 8px", color: "#e5e7eb", fontSize: "12px",
    pointerEvents: "none", display: "none", whiteSpace: "pre",
    lineHeight: "1.6", zIndex: "10",
  });
  el.appendChild(tooltip);

  // ── HTML control bar ────────────────────────────────────────────────────────

  const bar = document.createElement("div");
  bar.className = "bp-controls";

  const btnRestart   = document.createElement("button");
  btnRestart.textContent = "⏮";
  const btnPlayPause = document.createElement("button");
  btnPlayPause.textContent = "▶";

  const speedBtns = {};
  for (const s of [0.5, 1, 2, 4]) {
    const b = document.createElement("button");
    b.textContent = `${s}×`;
    b.dataset.speed = s;
    speedBtns[s] = b;
    b.addEventListener("click", () => {
      model.set("playback_speed", s);
      model.save_changes();
    });
  }

  const scrubber = document.createElement("input");
  scrubber.type = "range";
  scrubber.min = "0";
  scrubber.step = "0.01";

  const timeLabel = document.createElement("span");
  timeLabel.className = "bp-time";
  timeLabel.textContent = "0.0s";

  bar.appendChild(btnRestart);
  bar.appendChild(btnPlayPause);
  for (const b of Object.values(speedBtns)) bar.appendChild(b);
  bar.appendChild(scrubber);
  bar.appendChild(timeLabel);
  el.appendChild(bar);

  // ── Zoom / pan ─────────────────────────────────────────────────────────────

  let dragging = false, hasMoved = false;
  let dragStartX = 0, dragStartY = 0, worldStartX = 0, worldStartY = 0;

  app.view.addEventListener("wheel", (e) => {
    e.preventDefault();
    const factor = e.deltaY < 0 ? 1.1 : 0.9;
    const rect = app.view.getBoundingClientRect();
    const mx = e.clientX - rect.left, my = e.clientY - rect.top;
    world.scale.x *= factor;
    world.scale.y *= factor;
    world.x = mx - (mx - world.x) * factor;
    world.y = my - (my - world.y) * factor;
  }, { passive: false });

  app.view.addEventListener("mousedown", (e) => {
    dragging = true; hasMoved = false;
    dragStartX = e.clientX; dragStartY = e.clientY;
    worldStartX = world.x; worldStartY = world.y;
  });
  app.view.addEventListener("mousemove", (e) => {
    if (!dragging) return;
    const dx = e.clientX - dragStartX, dy = e.clientY - dragStartY;
    if (Math.sqrt(dx * dx + dy * dy) > 4) hasMoved = true;
    world.x = worldStartX + dx;
    world.y = worldStartY + dy;
  });
  ["mouseup", "mouseleave"].forEach((ev) =>
    app.view.addEventListener(ev, () => { dragging = false; })
  );

  // ── Animation state ─────────────────────────────────────────────────────────

  const nodeGfx    = {}; // id → PIXI.Graphics
  const nodeStates = {}; // id → { cur, prev, tChanged }
  // Cumulative activation counts (heatmap) — rebuilt on seek
  const actCounts  = {}; // id → int
  // Active edge particles: { x, y, vx, vy, startT }
  const particles  = []; // mutated in-place

  let internalT = 0.0;
  let prevT     = 0.0;
  let speed     = model.get("playback_speed") || 1.0;

  // Click-to-highlight
  let selectedNode = null;
  let pathNodes    = new Set();

  // ── Highlight helpers ───────────────────────────────────────────────────────

  function activeSet() {
    const explicit = model.get("highlighted_nodes") || [];
    if (!selectedNode && explicit.length === 0) return null;
    return new Set([...explicit, ...pathNodes]);
  }

  function drawEdges(active = null) {
    edgeLayer.clear();
    const { nodes, edges = [] } = model.get("graph_data") || {};
    if (!nodes) return;
    for (const e of edges) {
      const s = nodes[e.source], t = nodes[e.target];
      if (!s || !t) continue;
      const on = !active || (active.has(e.source) && active.has(e.target));
      const alpha = on ? 0.85 : DIM_ALPHA;
      e.type === "inhibition"
        ? drawBar(edgeLayer, s.x, s.y, t.x, t.y, EDGE_COLORS.inhibition, alpha)
        : drawArrow(edgeLayer, s.x, s.y, t.x, t.y, EDGE_COLORS.activation, alpha);
    }
  }

  // ── Tooltip ─────────────────────────────────────────────────────────────────

  function showTooltip(id, px, py) {
    const nodeInfo = (model.get("graph_data") || {}).nodes?.[id] || {};
    const ns = nodeStates[id];
    let html = `<strong>${id}</strong>`;
    if (nodeInfo.group) html += `\nGroup: ${nodeInfo.group}`;
    if (ns) html += `\nState: ${ns.cur === 1 ? "active" : "inactive"}`;
    if (actCounts[id]) html += `\nActivations: ${actCounts[id]}`;
    tooltip.innerHTML = html;
    const sx = world.scale.x;
    tooltip.style.left = `${px * sx + world.x + 16}px`;
    tooltip.style.top  = `${py * sx + world.y - 12}px`;
    tooltip.style.display = "block";
  }

  function hideTooltip() { tooltip.style.display = "none"; }

  // ── Node init ───────────────────────────────────────────────────────────────

  function initNodes() {
    nodeLayer.removeChildren();
    labelLayer.removeChildren();
    Object.keys(nodeGfx).forEach((k) => delete nodeGfx[k]);

    const gd = model.get("graph_data") || {};
    const { nodes } = gd;
    if (!nodes) return;
    const showLabels = model.get("show_labels");

    for (const [id, pos] of Object.entries(nodes)) {
      const g = new PIXI.Graphics();
      g.position.set(pos.x, pos.y);
      g.interactive = true;
      g.cursor = "pointer";

      g.on("mouseover", () => showTooltip(id, pos.x, pos.y));
      g.on("mouseout", hideTooltip);
      g.on("click", () => {
        if (hasMoved) return;
        hideTooltip();
        if (selectedNode === id) {
          selectedNode = null;
          pathNodes = new Set();
        } else {
          selectedNode = id;
          pathNodes = computePathNodes(id, gd.edges || []);
        }
        drawEdges(activeSet());
      });

      nodeLayer.addChild(g);
      nodeGfx[id] = g;

      if (showLabels) {
        const lbl = new PIXI.Text(id, { fontSize: 11, fill: 0xffffff, align: "center" });
        lbl.anchor.set(0.5, 2.2);
        lbl.position.set(pos.x, pos.y);
        labelLayer.addChild(lbl);
      }
    }
  }

  // ── Phase 7 — Glow ─────────────────────────────────────────────────────────

  function drawGlowLayer(t) {
    glowLayer.clear();
    if (!model.get("glow_enabled")) return;
    const { nodes } = model.get("graph_data") || {};
    if (!nodes) return;

    for (const [id, ns] of Object.entries(nodeStates)) {
      if (ns.cur !== 1) continue;
      const pos = nodes[id];
      if (!pos) continue;
      const elapsed = t - ns.tChanged;
      const intensity = elapsed < FADE_DUR ? easeInOut(elapsed / FADE_DUR) : 1.0;
      for (let i = GLOW_LAYERS; i >= 1; i--) {
        glowLayer.beginFill(GLOW_COLOR, 0.055 * intensity * i);
        glowLayer.drawCircle(pos.x, pos.y, NODE_RADIUS + i * 7);
        glowLayer.endFill();
      }
    }
  }

  // ── Phase 7 — Pulse rings ──────────────────────────────────────────────────

  function drawRingLayer(t) {
    ringLayer.clear();
    if (!model.get("pulse_ring_enabled")) return;
    const { nodes } = model.get("graph_data") || {};
    if (!nodes) return;

    for (const [id, ns] of Object.entries(nodeStates)) {
      if (ns.cur !== 1) continue;
      const pos = nodes[id];
      if (!pos) continue;
      const elapsed = t - ns.tChanged;
      if (elapsed < 0 || elapsed >= RING_DUR) continue;
      const progress = elapsed / RING_DUR;
      const r = NODE_RADIUS * (1.0 + progress * 2.5);
      const alpha = 0.65 * (1.0 - progress);
      ringLayer.lineStyle(1.8, ACTIVE_COLOR, alpha);
      ringLayer.beginFill(ACTIVE_COLOR, alpha * 0.12);
      ringLayer.drawCircle(pos.x, pos.y, r);
      ringLayer.endFill();
      ringLayer.lineStyle(0);
    }
  }

  // ── Phase 7 — Particles ────────────────────────────────────────────────────

  function spawnParticles(srcId, t) {
    const { nodes, edges = [] } = model.get("graph_data") || {};
    if (!nodes) return;
    const srcPos = nodes[srcId];
    if (!srcPos) return;
    for (const e of edges) {
      if (e.source !== srcId || e.type !== "activation") continue;
      const tgtPos = nodes[e.target];
      if (!tgtPos) continue;
      const dx = tgtPos.x - srcPos.x, dy = tgtPos.y - srcPos.y;
      const len = Math.sqrt(dx * dx + dy * dy) || 1;
      // spread 3 particles per edge with small lateral offsets
      for (let k = -1; k <= 1; k++) {
        particles.push({
          x: srcPos.x, y: srcPos.y,
          vx: dx / len, vy: dy / len,
          offX: -dy / len * k * 4, offY: dx / len * k * 4,
          totalDist: len - NODE_RADIUS * 2,
          startT: t,
        });
      }
    }
  }

  function drawParticleLayer(t) {
    partLayer.clear();
    if (!model.get("particles_enabled")) return;

    for (let i = particles.length - 1; i >= 0; i--) {
      const p = particles[i];
      const elapsed = t - p.startT;
      const progress = elapsed / PARTICLE_DUR;
      if (progress >= 1.0 || elapsed < 0) { particles.splice(i, 1); continue; }
      const dist = p.totalDist * progress;
      const px = p.x + p.vx * dist + p.offX;
      const py = p.y + p.vy * dist + p.offY;
      const alpha = progress < 0.3 ? progress / 0.3 : (1.0 - progress) / 0.7;
      partLayer.beginFill(EDGE_COLORS.activation, Math.max(0, alpha * 0.9));
      partLayer.drawCircle(px, py, 2.5);
      partLayer.endFill();
    }
  }

  // ── renderNodes ────────────────────────────────────────────────────────────

  function renderNodes(t) {
    const active  = activeSet();
    const heatmap = model.get("heatmap_enabled");

    // Max activations for heatmap normalisation
    let maxCount = 1;
    if (heatmap) {
      for (const v of Object.values(actCounts)) if (v > maxCount) maxCount = v;
    }

    for (const [id, g] of Object.entries(nodeGfx)) {
      const ns      = nodeStates[id] || { cur: 0, prev: 0, tChanged: -999 };
      const elapsed = t - ns.tChanged;

      // Base colour: heatmap or binary fade
      let color;
      if (heatmap) {
        const count = actCounts[id] || 0;
        const heat  = Math.min(count / maxCount, 1.0);
        const base  = lerpColor(INACTIVE_COLOR, HEAT_COLOR, heat);
        // Still fade to the heatmap colour on last transition
        if (elapsed < FADE_DUR) {
          const from = ns.prev === 1 ? lerpColor(INACTIVE_COLOR, HEAT_COLOR, heat) : INACTIVE_COLOR;
          color = lerpColor(from, base, easeInOut(elapsed / FADE_DUR));
        } else {
          color = base;
        }
      } else {
        if (elapsed >= FADE_DUR) {
          color = ns.cur === 1 ? ACTIVE_COLOR : INACTIVE_COLOR;
        } else {
          const fc = ns.prev === 1 ? ACTIVE_COLOR : INACTIVE_COLOR;
          const tc = ns.cur  === 1 ? ACTIVE_COLOR : INACTIVE_COLOR;
          color = lerpColor(fc, tc, easeInOut(elapsed / FADE_DUR));
        }
      }

      const scale =
        ns.cur === 1 && elapsed < PULSE_DUR
          ? 1 + 0.25 * Math.sin(Math.PI * elapsed / PULSE_DUR)
          : 1.0;

      g.clear();
      g.beginFill(color);
      g.drawCircle(0, 0, NODE_RADIUS);
      g.endFill();
      g.scale.set(scale, scale);
      g.alpha = active ? (active.has(id) ? 1.0 : DIM_ALPHA) : 1.0;
    }

    drawGlowLayer(t);
    drawRingLayer(t);
    drawParticleLayer(t);
  }

  // ── Event dispatch / seek ───────────────────────────────────────────────────

  function dispatch(ev) {
    const prev = nodeStates[ev.node];
    nodeStates[ev.node] = { cur: ev.state, prev: prev ? prev.cur : 0, tChanged: ev.t };
    if (ev.state === 1) {
      actCounts[ev.node] = (actCounts[ev.node] || 0) + 1;
      if (model.get("particles_enabled")) spawnParticles(ev.node, ev.t);
    }
  }

  function seekTo(t) {
    Object.keys(nodeStates).forEach((k) => delete nodeStates[k]);
    Object.keys(actCounts).forEach((k) => delete actCounts[k]);
    particles.length = 0;

    const events  = model.get("events_data") || [];
    const latest  = {};
    for (const ev of events) {
      if (ev.t <= t) {
        if (!latest[ev.node] || ev.t >= latest[ev.node].t) latest[ev.node] = ev;
        if (ev.state === 1) actCounts[ev.node] = (actCounts[ev.node] || 0) + 1;
      }
    }
    for (const ev of Object.values(latest)) {
      const prev = nodeStates[ev.node];
      nodeStates[ev.node] = { cur: ev.state, prev: prev ? prev.cur : 0, tChanged: ev.t };
    }
    internalT = t;
    prevT     = t;
  }

  // ── Control bar ─────────────────────────────────────────────────────────────

  function updateControls() {
    const state    = model.get("playback_state");
    btnPlayPause.textContent = state === "playing" ? "⏸" : "▶";
    const curSpeed = model.get("playback_speed");
    for (const [s, b] of Object.entries(speedBtns)) {
      b.classList.toggle("bp-active", parseFloat(s) === curSpeed);
    }
    const dur = model.get("duration") || 0;
    scrubber.max   = String(Math.max(dur, 0.01));
    scrubber.value = String(internalT);
    timeLabel.textContent = `${internalT.toFixed(1)}s`;
  }

  btnRestart.addEventListener("click", () => {
    seekTo(0);
    renderNodes(0);
    drawEdges(activeSet());
    model.set("playback_state", "idle");
    model.set("current_t", 0);
    model.save_changes();
    updateControls();
  });

  btnPlayPause.addEventListener("click", () => {
    const next = model.get("playback_state") === "playing" ? "paused" : "playing";
    model.set("playback_state", next);
    model.save_changes();
  });

  let scrubbing = false;
  scrubber.addEventListener("mousedown", () => { scrubbing = true; });
  scrubber.addEventListener("input", () => {
    if (!scrubbing) return;
    const t = parseFloat(scrubber.value);
    seekTo(t);
    renderNodes(internalT);
    drawEdges(activeSet());
    timeLabel.textContent = `${internalT.toFixed(1)}s`;
  });
  scrubber.addEventListener("mouseup", () => {
    scrubbing = false;
    model.set("current_t", internalT);
    model.save_changes();
  });

  // ── Animation ticker ────────────────────────────────────────────────────────

  app.ticker.maxFPS = 60;
  app.ticker.add((delta) => {
    if (model.get("playback_state") !== "playing") return;
    if (scrubbing) return;

    const newT = internalT + (delta / 60) * speed;
    const events = model.get("events_data") || [];
    for (const ev of events) {
      if (ev.t > prevT && ev.t <= newT) dispatch(ev);
    }

    prevT     = internalT;
    internalT = newT;
    renderNodes(internalT);

    const dur = model.get("duration") || 0;
    if (internalT >= dur + 0.5) {
      internalT = dur + 0.5;
      model.set("playback_state", "paused");
      model.set("current_t", internalT);
      model.save_changes();
    }
    updateControls();
  });

  // ── Model listeners ─────────────────────────────────────────────────────────

  model.on("change:graph_data", () => {
    drawEdges(activeSet());
    initNodes();
    renderNodes(internalT);
  });
  model.on("change:show_labels", () => {
    initNodes();
    drawEdges(activeSet());
    renderNodes(internalT);
  });
  model.on("change:playback_state", () => {
    if (model.get("playback_state") === "idle") {
      seekTo(0);
      renderNodes(0);
    }
    updateControls();
  });
  model.on("change:current_t", () => {
    const t = model.get("current_t");
    if (Math.abs(t - internalT) > 0.05) {
      seekTo(t);
      renderNodes(internalT);
      drawEdges(activeSet());
      updateControls();
    }
  });
  model.on("change:playback_speed", () => {
    speed = model.get("playback_speed");
    updateControls();
  });
  model.on("change:highlighted_nodes", () => {
    renderNodes(internalT);
    drawEdges(activeSet());
  });
  // Phase 7 effect toggles — redraw on change
  for (const key of ["glow_enabled", "pulse_ring_enabled", "heatmap_enabled", "particles_enabled"]) {
    model.on(`change:${key}`, () => renderNodes(internalT));
  }

  // ── Initial render ──────────────────────────────────────────────────────────

  drawEdges();
  initNodes();
  renderNodes(0);
  updateControls();

  return () => app.destroy(true);
}
