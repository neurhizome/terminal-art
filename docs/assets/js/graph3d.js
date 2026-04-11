/**
 * graph3d.js — Force-directed 3D knowledge graph
 *
 * The same topology that lives as ANSI art in the terminal, rendered in
 * three-dimensional space. Nodes are posts and concepts; edges are the
 * [[related]] links that tie one idea to another. The layout emerges from
 * the force simulation — we don't plan it.
 *
 * Design intent:
 *   - The two-column metaphor of the ANSI graph is preserved as a soft
 *     bias force, not a hard constraint. Sessions cluster left, concepts
 *     cluster right, but cross-links can pull nodes across the divide.
 *   - Within the session column, time runs along the z-axis. Earlier
 *     posts sit further back; newer ones come forward.
 *   - Edge particles flow along connections like scent trails — the same
 *     diffusion aesthetic as the walker simulations.
 *   - Once the force simulation settles, the camera begins a slow orbit.
 *     The graph breathes.
 *
 * Colors match graph_viz.py exactly:
 *   beginning → #e5c07b  (amber)
 *   session   → #61afef  (blue)
 *   gradient  → #98c379  (green)
 *   concept   → #c678dd  (purple)
 *
 * Depends on:
 *   3d-force-graph (loaded from CDN — bundles Three.js + d3-force-3d)
 *   knowledge-graph.json (emitted by tools/graph_viz.py alongside the .ans)
 */

(function () {
  'use strict';

  // Jekyll injects window.SITE_BASEURL before this script loads
  const BASE = (typeof window.SITE_BASEURL !== 'undefined' && window.SITE_BASEURL)
    ? window.SITE_BASEURL : '';

  // ── Palette — exact values from graph_viz.py ─────────────────────────────
  const NODE_COLORS = {
    beginning: '#e5c07b',
    session:   '#61afef',
    gradient:  '#98c379',
    concept:   '#c678dd',
  };

  const NODE_GLYPHS = {
    beginning: '◈',
    session:   '◆',
    gradient:  '◉',
    concept:   '◇',
  };

  function nodeColor(n) {
    return NODE_COLORS[n.type] || '#abb2bf';
  }

  // Degree-weighted size: hubs are visually larger
  function nodeVal(n) {
    return 4 + Math.sqrt(Math.max(n.connections || 0, 0)) * 2.8;
  }

  // HTML tooltip rendered on hover
  function nodeLabel(n) {
    const c     = nodeColor(n);
    const glyph = NODE_GLYPHS[n.type] || '·';
    const sub   = n.date || n.type;
    return [
      `<div style="`,
      `background:rgba(17,21,28,0.96);`,
      `border:1px solid ${c};`,
      `border-radius:4px;`,
      `padding:7px 12px;`,
      `font-family:'IBM Plex Mono',monospace;`,
      `font-size:12px;`,
      `line-height:1.6;`,
      `max-width:260px;`,
      `pointer-events:none;`,
      `">`,
      `<div style="color:${c};font-weight:600;margin-bottom:2px">`,
      `${glyph}&nbsp;${n.label}`,
      `</div>`,
      `<div style="color:#4b5263;font-size:11px">`,
      `${sub}&nbsp;·&nbsp;${n.connections || 0} edge${n.connections === 1 ? '' : 's'}`,
      `</div>`,
      `</div>`,
    ].join('');
  }

  // ── Custom force: column bias + temporal depth ────────────────────────────
  //
  // This implements the d3-force protocol (initialize + callable with alpha)
  // without importing d3 — so it works regardless of what the CDN bundle exposes.
  //
  // Column bias: sessions/beginning pull left (x = -120), concepts/gradient pull right.
  // Temporal depth: session nodes pull along z proportional to days since first post.

  const EPOCH_MS   = new Date('2026-02-18').getTime();
  const MS_PER_DAY = 86_400_000;
  const COLUMN_STRENGTH = 0.07;
  const DEPTH_STRENGTH  = 0.03;

  function makeLayoutForce() {
    let nodes;

    function targetX(n) {
      return (n.type === 'concept' || n.type === 'gradient') ? 130 : -130;
    }

    function targetZ(n) {
      if (!n.date) return 0;
      const days = (new Date(n.date).getTime() - EPOCH_MS) / MS_PER_DAY;
      return days * 3.5;
    }

    function force(alpha) {
      for (const n of nodes) {
        n.vx += (targetX(n) - n.x) * COLUMN_STRENGTH * alpha;
        n.vz += (targetZ(n) - (n.z || 0)) * DEPTH_STRENGTH * alpha;
      }
    }

    force.initialize = function (_nodes) { nodes = _nodes; };
    return force;
  }

  // ── Main initialisation ───────────────────────────────────────────────────

  async function initGraph(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const loadingEl = document.getElementById('graph-3d-loading');
    const statsEl   = document.getElementById('graph-3d-stats');

    // Fetch the pre-generated graph data
    let data;
    try {
      const url = `${BASE}/assets/captures/knowledge-graph.json`;
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status} fetching ${url}`);
      data = await res.json();
    } catch (err) {
      console.error('[graph3d] fetch failed:', err);
      if (loadingEl) {
        loadingEl.innerHTML =
          `<span style="color:#e06c75">could not load graph: ${err.message}</span>`;
      }
      return;
    }

    if (loadingEl) loadingEl.style.display = 'none';

    // ── Build the scene ───────────────────────────────────────────────────────
    const Graph = ForceGraph3D({ controlType: 'orbit' })(container)
      .backgroundColor('#11151c')
      .graphData(data)

      // Nodes
      .nodeColor(nodeColor)
      .nodeVal(nodeVal)
      .nodeOpacity(0.92)
      .nodeResolution(16)
      .nodeLabel(nodeLabel)

      // Edges — scent trails with flowing particles
      .linkColor(() => 'rgba(88,108,140,0.30)')
      .linkWidth(0.7)
      .linkDirectionalParticles(2)
      .linkDirectionalParticleWidth(1.4)
      .linkDirectionalParticleColor(() => 'rgba(97,175,239,0.65)')
      .linkDirectionalParticleSpeed(0.0028)

      // Navigation: click a node → visit the post
      .onNodeClick(node => {
        if (node.url) {
          window.location.href = BASE + node.url;
        }
      })

      // Start pulled back — let the emergence be visible
      .cameraPosition({ x: 0, y: 20, z: 460 });

    // Tune the default repulsion so the graph breathes
    Graph.d3Force('charge').strength(-110);

    // Apply the column + temporal bias force
    Graph.d3Force('layout-bias', makeLayoutForce());

    // ── Gentle orbit once the simulation has settled ──────────────────────────
    let userHasInteracted = false;
    let orbitHandle = null;

    function stopOrbit() {
      userHasInteracted = true;
      if (orbitHandle) {
        clearInterval(orbitHandle);
        orbitHandle = null;
      }
    }

    ['mousedown', 'touchstart', 'wheel'].forEach(evt =>
      container.addEventListener(evt, stopOrbit, { passive: true })
    );

    Graph.onEngineStop(() => {
      if (orbitHandle || userHasInteracted) return;

      // Snap the orbit angle to the camera's current azimuth
      const pos = Graph.cameraPosition();
      let angle = Math.atan2(pos.x, pos.z);
      const r   = Math.sqrt(pos.x ** 2 + pos.z ** 2) || 400;
      const cy  = pos.y * 0.5; // drift slowly toward equator

      orbitHandle = setInterval(() => {
        if (userHasInteracted) return;
        angle += 0.0016;
        Graph.cameraPosition({
          x: r * Math.sin(angle),
          y: cy,
          z: r * Math.cos(angle),
        });
      }, 50);
    });

    // ── Stats bar ─────────────────────────────────────────────────────────────
    if (statsEl) {
      const gen = (data.generated || '').slice(0, 10);
      statsEl.innerHTML =
        Object.entries(NODE_COLORS).map(([type, color]) =>
          `<span style="color:${color}">${NODE_GLYPHS[type]} ${type}</span>`
        ).join('<span style="color:#2c313c"> · </span>') +
        `<span style="color:#2c313c"> &nbsp;|&nbsp; </span>` +
        `<span style="color:#4b5263">${data.nodes.length} nodes · ` +
        `${data.links.length} edges · ${gen}</span>`;
    }
  }

  // ── Entry point: wait for both DOM and ForceGraph3D library ──────────────
  function tryInit() {
    if (typeof ForceGraph3D !== 'undefined') {
      initGraph('graph-3d');
    } else {
      setTimeout(tryInit, 80);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', tryInit);
  } else {
    tryInit();
  }

}());
