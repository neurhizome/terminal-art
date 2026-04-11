---
layout: default
title: "Knowledge Graph"
permalink: /graph/
---

<div class="concept-note">

<div class="concept-header">
  <span class="concept-tag">meta</span>
  <h1 class="concept-title">Knowledge Graph</h1>
  <p class="concept-subtitle">The topology of this blog rendered in two media. The same data, the same edges — one lives in the terminal, one in the browser. Each is true to its substrate.</p>
</div>

<!-- ── 3D force-directed graph ─────────────────────────────────────────── -->

<div style="position:relative;width:100%;height:680px;background:#11151c;border-radius:6px;overflow:hidden;margin-bottom:0.5rem">
  <div id="graph-3d" style="width:100%;height:100%"></div>
  <div id="graph-3d-loading" style="
    position:absolute;top:50%;left:50%;
    transform:translate(-50%,-50%);
    color:#4b5263;
    font-family:'IBM Plex Mono',monospace;
    font-size:0.85rem;
    letter-spacing:0.05em;
  ">initializing force simulation…</div>
</div>

<div id="graph-3d-stats" style="
  font-family:'IBM Plex Mono',monospace;
  font-size:0.78rem;
  color:#4b5263;
  padding:0.4rem 0.2rem 1.4rem;
  line-height:1.4;
">&nbsp;</div>

<!-- 3d-force-graph bundles Three.js and d3-force-3d — loaded only on this page -->
<script src="https://unpkg.com/3d-force-graph@1.73.4/dist/3d-force-graph.min.js"></script>
<script src="{{ '/assets/js/graph3d.js' | relative_url }}"></script>

<!-- ── How It Works ────────────────────────────────────────────────────── -->

<div style="margin-bottom:2rem">

The graph updates itself. Every commit that touches a post or concept file triggers
<code>tools/graph_viz.py</code>, which re-parses the frontmatter, rebuilds the topology,
and writes two artifacts: the ANSI terminal render below and the
<code>knowledge-graph.json</code> that feeds the 3D view above.

The **force simulation** finds the layout — nothing is hardcoded. A soft bias pulls
session posts left and concept pages right, mirroring the ANSI graph's two-column
structure. Within the session cluster, time runs along the z-axis; older posts sit
further back, newer ones come forward. The y-axis is free — pure emergence. Nodes
that share many cross-column edges bridge the two spaces visually.

**Drag** to rotate. **Scroll** to zoom. **Click** any node to visit that post or concept.
The camera will begin a slow orbit once the simulation settles.

</div>

<!-- ── Terminal artifact ────────────────────────────────────────────────── -->

<details style="margin-bottom:2rem">
<summary style="
  cursor:pointer;
  font-family:'IBM Plex Mono',monospace;
  font-size:0.88rem;
  color:#4b5263;
  padding:0.5rem 0;
  border-top:1px solid #2c313c;
  list-style:none;
  user-select:none;
">
  <span style="color:#38b6c2">▶</span>&nbsp;terminal artifact — knowledge-graph.ans
</summary>

<div style="margin-top:1rem">

<div class="capture-block">
<div class="terminal-wrapper">
<div id="cap-graph" class="terminal-display"></div>
</div>
</div>
<script>renderCapture('knowledge-graph.ans', 'cap-graph');</script>

<div class="capture-meta" style="margin-top:0.75rem">
  <strong>knowledge-graph.ans</strong> — 96 cols, auto-height. The same topology,
  rendered with box-drawing characters in 24-bit colour. Rebuilt on every qualifying
  commit via the <code>.git/hooks/post-commit</code> hook.
  <ul style="margin-top:0.5rem">
    <li>left column: chronological spine (sessions sorted by date)</li>
    <li>right column: concept space (concepts + aesthetic posts)</li>
    <li>horizontal connectors: cross-column <code>related:</code> links</li>
    <li>vertical dotted lines: same-column concept links</li>
  </ul>
</div>

</div>
</details>

<!-- ── Sleep Cycle note ─────────────────────────────────────────────────── -->

## Sleep Cycle

The graph doesn't just track what exists — eventually it will *compress* it. When a
cluster of tightly-linked nodes builds up, the graph could fold the cluster into a
topological knot: a single node representing the attractor that cluster has converged
to. High-density regions collapse into concepts. The knowledge graph runs its own
diffusion, and the sleep cycle is the global update step.

In the 3D view this compression would manifest as nodes physically merging — their
geometries spiralling inward toward a shared point. The edge particles would converge
on the knot. What was a cluster becomes a single emitter.

That compression pass isn't implemented. But the infrastructure is here, and the
3D medium makes it easier to see what the ANSI graph could only imply.

</div>
