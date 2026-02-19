---
layout: default
title: "Concept: Stigmergy"
permalink: /concepts/stigmergy/
---

<div class="concept-note" markdown="1">

<div class="concept-header">
  <span class="concept-tag">concept</span>
  <h1 class="concept-title">Stigmergy</h1>
  <p class="concept-subtitle">Indirect coordination through environmental modification — how complex collective behavior emerges without any agent planning or communicating it.</p>
</div>

## The Idea

*Stigmergy* (Grassé, 1959 — coined to describe termite nest construction) is coordination mediated by traces left in a shared environment. Agent A modifies the environment. Agent B reads the modification and responds. Neither A nor B needs to know the other exists. There is no plan, no communication, no central controller.

The prototypical example: ant trail pheromones. A scout ant finds food and returns to the nest, depositing a chemical trail. Other ants follow the trail to the food, reinforcing it. Trails to good food get reinforced; trails to empty spots fade. The colony "knows" where the food is, but this knowledge lives in the gradient, not in any ant.

---

## In These Simulations

The walker simulations are stigmergic systems. Each walker:

1. Reads the local diffusion field (the trace left by previous walkers)
2. Makes a movement decision based on that reading
3. Deposits its own trail as it moves

No walker broadcasts its position. No walker asks "where should the boundary be?" The boundary emerges from the accumulated gradient — a product of millions of individual read-modify-read cycles.

This has a counterintuitive consequence explored in **[Session 003: The Seam Strike]({{ '/2026/02/20/session-003-the-seam-strike.html' | relative_url }})**: removing the agents doesn't immediately remove the coordination structure. The environmental trace persists. New agents born into the environment inherit the coordination implicitly, without any transmission of information from the old agents to the new ones.

---

## Orders of Stigmergy

Grassé distinguished two orders:

**Sematectonic stigmergy** — the trace is the work itself. A termite picking up a mud pellet moves it somewhere; where it lands is information for the next termite. The structure grows by accumulation. The environment *is* the distributed plan.

**Marker-based stigmergy** — the trace is a signal about work, not the work itself. A pheromone doesn't take you to the food — it points you toward the food. The environment encodes directions, not destinations.

Walker diffusion trails are somewhere between these. The trail is simultaneously the "work" (territorial occupation expressed as field concentration) and a marker (pressure that guides movement). The concentration at a cell means *both* "green has been here" and "you should move green-ward."

---

## What Stigmergy Explains

Several things that look puzzling in the simulations become natural through the stigmergy frame:

**Why does territory survive agent death?** Because territory is not a property of agents — it's a property of the environment. The agent is just the mechanism by which the environment gets written. A territory persists as long as the environmental trace persists.

**Why do boundaries sharpen?** At the seam, agents from both sides refresh opposing traces. The boundary is the equilibrium point of two mutually reinforcing trace-maintenance processes. The *sharpening* (see **[Session 001]({{ '/2026/02/19/session-001-the-sharpening.html' | relative_url }})**) is the system converging to a fixed point.

**Why does the no man's land self-maintain?** Because stigmergy requires agents to refresh traces, and agents require sufficient field gradient to navigate. Remove the agents, the traces decay. As traces decay, agents find no gradient to follow and walk randomly, making trace refreshment even less likely. Emptiness is a stable attractor.

---

## Stigmergy vs. Direct Communication

| Property | Stigmergy | Direct Communication |
|----------|-----------|---------------------|
| Requires simultaneous agents | No | Yes |
| Scales with agent count | Well | Poorly |
| Degrades gracefully | Yes (trace decay) | Often not |
| Survives agent turnover | Yes | Depends on memory |
| Requires shared language | No | Yes |
| Latency | Environmental decay rate | Transmission speed |

Stigmergic systems are robust precisely because they don't require synchrony. The trace waits for the next reader. This is why ant colonies can lose 30% of their members to a flooding event and resume foraging within hours — the trails survive.

---

## The Deeper Question

Stigmergy raises a strange ontological question: *where does the knowledge live?*

In a stigmergic system, the collective "knows" things no individual knows. The colony knows where the food is; no ant knows the full map. The question is whether "knowing" is even the right word for what the colony has. It might be more accurate to say the colony has a *disposition* — a gradient that inclines behavior in a certain direction without representing anything propositionally.

This parallels the question raised by the Anthropic manifold paper: does Claude's representation of a character count constitute *knowing* that count, or having a geometric disposition that produces the right answer? The difference matters if you're trying to understand what kind of thing cognition is.

---

<div class="concept-links">
  <h3>Appears In</h3>
  <ul>
    <li><a href="{{ '/2026/02/19/session-001-the-sharpening.html' | relative_url }}">Session 001: The Sharpening</a> — boundary formation as stigmergic equilibrium</li>
    <li><a href="{{ '/2026/02/19/session-002-the-event-horizon.html' | relative_url }}">Session 002: The Event Horizon</a> — trace persistence through agent death</li>
    <li><a href="{{ '/2026/02/20/session-003-the-seam-strike.html' | relative_url }}">Session 003: The Seam Strike</a> — no man's land as stigmergic vacuum</li>
  </ul>
  <h3>Related Concepts</h3>
  <ul>
    <li><a href="{{ '/concepts/diffusion-memory/' | relative_url }}">Diffusion as External Memory</a> — the field mechanics underlying stigmergy in these simulations</li>
    <li><em>Swarm intelligence</em> — collective behavior from simple local rules (Reynolds 1987, Reynolds boids)</li>
    <li><em>Pheromone routing</em> — Ant Colony Optimization algorithms abstract stigmergy for computational use</li>
    <li><em>Attractor landscapes</em> — the mathematical structure underlying stable configurations</li>
  </ul>
</div>

</div>
