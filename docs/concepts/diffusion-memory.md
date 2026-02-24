---
layout: default
title: "Concept: Diffusion as External Memory"
permalink: /concepts/diffusion-memory/
---

<div class="concept-note" markdown="1">

<div class="concept-header">
  <span class="concept-tag">concept</span>
  <h1 class="concept-title">Diffusion as External Memory</h1>
  <p class="concept-subtitle">How a gradient field encodes territorial knowledge without any agent "knowing" the territory.</p>
</div>

## The Basic Setup

In these simulations, each walker has a genome that determines its color. When a walker occupies a cell, it deposits a small concentration of its color into the diffusion field at that position. The field then evolves autonomously each tick:

```
field[x][y] = field[x][y] * (1 - decay) + Σ neighbor_contributions * diffusion_rate
```

No walker reads from the field to "know" who owns which territory. Instead, walkers sense local field concentration and use it to modulate their movement: high same-color concentration → continue; high other-color concentration → increased turn probability. The territory "knowledge" is in neither the walkers nor their behaviors — it's in the **accumulated shape of the field itself**.

---

## Field Inertia

The diffusion field has persistence independent of its agents. A cell's concentration decays slowly (typically `decay ≈ 0.02` per tick). At `diffusion=0.15`, a green walker stepping on a cell contributes roughly 0.85 of its value to neighbors — spreading the signal, but also distributing the load.

Consequence: if you remove all walkers from a region, the field remains informative for hundreds of ticks. New walkers entering that region sense the old gradient and behave accordingly. The territory survives the death of every agent that created it.

This is the mechanism explored in **[Session 002: The Event Horizon]({{ '/2026/02/19/session-002-the-event-horizon.html' | relative_url }})** — a mass-extinction cascade that killed 60% of green walkers failed to erase the boundary because the field remembered.

---

## The Diffusion Rate as a Parameter

The `diffusion` parameter controls how fast the field spreads (and therefore how fast it blurs):

| Rate | Effect |
|------|--------|
| `0.05` | Trail stays local, sharp gradients, slow to spread |
| `0.15` | Moderate spread, boundary forms and *sharpens* (see Session 001) |
| `0.20` | Rapid spread, territories blur faster than walkers can reinforce |

At `0.15`, there's a critical regime: the gradient spreads fast enough to fill gaps in walker coverage, but slow enough that concentrated core regions create steep walls. This is why boundaries sharpen rather than blur at this rate — the seam is a region where two opposing gradients are in competitive equilibrium.

**[Session 001: The Sharpening]({{ '/2026/02/19/session-001-the-sharpening.html' | relative_url }})** explores this parameter directly.

---

## External vs. Internal Memory

The diffusion field is an example of **stigmergy** — indirect coordination through environmental modification. The field is:

- **External**: lives outside the agents, in the grid
- **Spatial**: encoded as position, not symbol
- **Distributed**: no single cell holds all the information
- **Decaying**: the memory degrades without reinforcement

This contrasts with *internal* memory — a representation stored inside an agent (or model). When Anthropic researchers studying Claude 3.5 Haiku found that it represents scalar quantities as [curved geometric manifolds](https://arxiv.org/abs/2502.09696) in its activation space, they found a form of internal memory that is:

- **Internal**: lives inside the model's weights and activations
- **Geometric**: encoded as shape in a high-dimensional space
- **Localized**: concentrated in specific activation subspaces
- **Persistent**: doesn't decay (within a forward pass)

The interesting comparison: which representation is more **robust to perturbation**? The external field survives agent death but is vulnerable to sustained absence of reinforcement. The internal manifold survives context variation but may shift with distribution shift. Both encode "where is the boundary" as a geometric structure rather than an explicit rule.

---

## The Memory is the Territory

A useful reframe: in these simulations, **the diffusion field *is* the territory**. The walkers are the territory's maintenance process. They are not the territory itself.

This creates a strange inversion: the "knowledge" of territorial ownership is not held by any individual, not encoded in any genome, not present in any behavior rule. It emerges from accumulation and persists through inertia. A territory is not a belief or a rule — it is a residue.

An open question: can a territory be created without agents? Could you seed the field directly, bypass the walker accumulation process, and produce a "fake" territory that walkers would behave as if they'd built? Probably yes. And if so, what does that imply about the relationship between a culture's "content" (field concentration) and its "history" (the walkers who made it)?

---

<div class="concept-links">
  <h3>Appears In</h3>
  <ul>
    <li><a href="{{ '/2026/02/19/session-001-the-sharpening.html' | relative_url }}">Session 001: The Sharpening</a> — boundary sharpening at diffusion=0.15</li>
    <li><a href="{{ '/2026/02/19/session-002-the-event-horizon.html' | relative_url }}">Session 002: The Event Horizon</a> — field inertia under event perturbation</li>
    <li><a href="{{ '/2026/02/20/session-003-the-seam-strike.html' | relative_url }}">Session 003: The Seam Strike</a> — no man's land as region where field memory was destroyed and not rebuilt</li>
    <li><a href="{{ '/2026/02/20/the-predator-and-the-pulse.html' | relative_url }}">The Predator and the Pulse</a> — field as lag indicator: predators hunting a ghost; memory accurate in aggregate but wrong for any specific follower</li>
    <li><a href="{{ '/2026/02/21/session-006-wolf-interval.html' | relative_url }}">Session 006: Wolf Interval</a> — resonance scent as diffusion memory in pitch space; the topology of the circle of fifths encoded in accumulated fifth-encounter records, not in any walker</li>
  </ul>
  <h3>Related Concepts</h3>
  <ul>
    <li><em>Stigmergy</em> — indirect coordination via environmental modification (Grasse 1959)</li>
    <li><em>Attractor landscapes</em> — stable configurations in dynamical systems</li>
    <li><em>Place cells</em> — hippocampal encoding of spatial position; the manifold paper finds analogous structure in Claude's activations</li>
  </ul>
</div>

</div>
