/**
 * BioPulse static graph renderer — PixiJS v7.
 *
 * Phase 4 interactions:
 *   - Scroll to zoom, drag to pan (world container)
 *   - Hover node → HTML tooltip (id, group)
 *   - Click node → BFS upstream + downstream path highlight; click again to clear
 *   - highlighted_nodes traitlet: Python can drive highlights programmatically
 *
 * graph_data format:
 *   { nodes: {[id]: {x, y, group?}}, edges: [{source, target, type}] }
 */

import * as PIXI from "https://esm.sh/pixi.js@7";

const NODE_RADIUS = 12;
const NODE_COLOR = 0x4fc3f7;
const INACTIVE_COLOR = 0x2d5986;
const EDGE_COLORS = { activation: 0x7ec8e3, inhibition: 0xff6b6b };
const BG_COLOR = 0x1a1a2e;
const DIM_ALPHA = 0.12;
const GLOW_COLOR = 0x4fc3f7;
const GLOW_LAYERS = 4;

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
  const width = model.get("width");
  const height = model.get("height");

  const app = new PIXI.Application({
    width, height, backgroundColor: BG_COLOR, antialias: true,
    resolution: (typeof window !== "undefined" && window.devicePixelRatio) || 1,
    autoDensity: true,
  });
  el.style.position = "relative";
  el.appendChild(app.view);

  // World container — zoom/pan target
  const world = new PIXI.Container();
  app.stage.addChild(world);

  const glowLayer  = new PIXI.Graphics();
  const edgeLayer  = new PIXI.Graphics();
  const nodeLayer  = new PIXI.Container();
  const labelLayer = new PIXI.Container();
  world.addChild(glowLayer);
  world.addChild(edgeLayer);
  world.addChild(nodeLayer);
  world.addChild(labelLayer);

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

  // Per-node sprite refs
  const nodeGfx = {}; // id → PIXI.Graphics
  let selectedNode = null;
  let pathNodes = new Set();

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

  // ── Highlight helpers ───────────────────────────────────────────────────────

  function activeSet() {
    const explicit = model.get("highlighted_nodes") || [];
    if (!selectedNode && explicit.length === 0) return null;
    const combined = new Set([...explicit, ...pathNodes]);
    return combined;
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

  function drawGlow(active) {
    glowLayer.clear();
    if (!model.get("glow_enabled") || !active) return;
    const { nodes } = model.get("graph_data") || {};
    if (!nodes) return;
    for (const id of active) {
      const pos = nodes[id];
      if (!pos) continue;
      for (let i = GLOW_LAYERS; i >= 1; i--) {
        glowLayer.beginFill(GLOW_COLOR, 0.06 * i);
        glowLayer.drawCircle(pos.x, pos.y, NODE_RADIUS + i * 7);
        glowLayer.endFill();
      }
    }
  }

  function applyHighlight() {
    const active = activeSet();
    for (const [id, g] of Object.entries(nodeGfx)) {
      g.alpha = active ? (active.has(id) ? 1.0 : DIM_ALPHA) : 1.0;
    }
    drawEdges(active);
    drawGlow(active);
  }

  // ── Tooltip helpers ─────────────────────────────────────────────────────────

  function showTooltip(id, px, py) {
    const nodeInfo = (model.get("graph_data") || {}).nodes?.[id] || {};
    let html = `<strong>${id}</strong>`;
    if (nodeInfo.group) html += `\nGroup: ${nodeInfo.group}`;
    tooltip.innerHTML = html;
    const sx = world.scale.x;
    tooltip.style.left = `${px * sx + world.x + 16}px`;
    tooltip.style.top  = `${py * sx + world.y - 12}px`;
    tooltip.style.display = "block";
  }

  function hideTooltip() { tooltip.style.display = "none"; }

  // ── Node setup ──────────────────────────────────────────────────────────────

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
      g.beginFill(NODE_COLOR);
      g.drawCircle(0, 0, NODE_RADIUS);
      g.endFill();
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
        applyHighlight();
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

  // ── Model listeners ─────────────────────────────────────────────────────────

  function redraw() {
    drawEdges();
    initNodes();
    applyHighlight();
  }

  model.on("change:graph_data", redraw);
  model.on("change:show_labels", redraw);
  model.on("change:highlighted_nodes", applyHighlight);
  model.on("change:glow_enabled", applyHighlight);

  // ── Initial render ──────────────────────────────────────────────────────────

  redraw();

  return () => app.destroy(true);
}
