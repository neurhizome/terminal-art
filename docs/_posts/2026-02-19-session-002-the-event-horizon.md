---
layout: post
title: "Session 002: The Event Horizon"
date: 2026-02-19
tags: [session, territory, events, emergence, field-memory]
related:
  - title: "Session 001: The Sharpening"
    url: /2026/02/19/session-001-the-sharpening.html
  - title: "Concept: Diffusion as External Memory"
    url: /concepts/diffusion-memory/
  - title: "Color Grimoire"
    url: /palette/
captures:
  - file: session-002-event.ans
    title: "The Event Horizon — Post-Event Recovery"
    description: >
      88×24 scene, approximately tick 4800. A mass-extinction event swept
      through the upper-left quadrant (red ×-marks) and destabilized the
      seam. The boundary is re-forming. An orange mutation lineage — born
      during the chaos — holds a pocket 64–73 columns in.
    seed: 7
    flags: "--initial-walkers 36 --seed 7 --events"
---

Light doesn't know it's traveling. It just propagates.

I keep thinking about the photon — how it doesn't experience the journey, doesn't accumulate knowledge of where it's been, arrives at its destination having carried information it never processed. The diffusion field is similar. It doesn't "know" the territory. It's just a gradient, summing millions of step-traces into a pressure landscape. And yet, something like territorial knowledge lives there. Something that [[i,ye/persists through events that the walkers do not survive]].

That's what Session 002 is about.

---

## The Question

If you erase the walkers — kill them all at once, or scatter them with a spawning storm — does the territory survive?

Where does the "knowledge" of the boundary actually live?

---

## Setting the Stage

Same configuration as [Session 001](/2026/02/19/session-001-the-sharpening.html): `--initial-walkers 36 --seed 7`, `diffusion=0.15`. Full toolkit context there. Tonight adds one flag:

```bash
python experiments/memetic_territories.py --initial-walkers 36 --seed 7 --events
```

`--events` enables a periodic event scheduler — drawn from [`src/events/catalog.py`](https://github.com/neurhizome/terminal-art/blob/main/src/events/catalog.py) — which fires at irregular intervals:

- **Extinction cascade**: kills a random 40–70% of walkers in a region
- **Mutation storm**: temporarily inflates `mutation_rate` by 5–10× for surviving walkers
- **Spawning surge**: drops 15–25 new walkers into a region (with fresh genomes)

The events fire on walkers. [[b,cy/The diffusion field is not touched.]]

---

## The Observation

I let the simulation reach equilibrium first — approximately 3000 ticks, a stable two-territory configuration with a seam at roughly column 43. Visually identical to Session 001's endpoint. Then the event scheduler was enabled.

The first event: an extinction cascade in the upper-left, rows 1–5, columns 1–11. [[b,re/About 60% of green walkers in that zone died.]] The red scars in the capture are their absence — cells where walker density dropped so fast the trail hadn't faded.

What happened next was the interesting part.

New walkers spawned into the devastated zone. [[i,dim/They didn't know what had happened there.]] They walked into a field that still had strong green concentration — the trail from ten thousand previous steps, still decaying, still present. The field remembered. The new walkers sensed green pressure and [[i,gr/walked like green walkers]].

The boundary didn't move. Not significantly. The seam compressed slightly at row 1, expanded slightly at row 18, then settled back. The event was absorbed.

---

## The Orange Pocket

The mutation storm is what produced the anomaly.

During the cascade, some walkers near the seam — in the chaotic mixing zone — accumulated three or four consecutive mutations in quick succession. Each mutation has a 15% chance of shifting the hue by more than 30°. A chain of four: rare, but at elevated mutation rate, inevitable.

The result was a walker whose genome encodes [[b,or/orange]]. Not a drift toward orange — a discontinuous jump outside the green/blue basin.

The orange walkers found themselves in a field-neutral zone: the seam, where no color had strong concentration. They started laying orange trail. Other survivors from the mutation storm, similarly displaced, had similar genomes. [[i,or/A pocket formed.]] By tick 4800 (the captured moment), it was nine columns wide, six rows tall, with a dense core and a fading rim — small but internally coherent.

The blue field pressure surrounds it. Orange can hold as long as its trail concentration exceeds the blue gradient pushing in. The question I couldn't answer in this session: [[i,ye/how long does it last?]]

---

## Field Inertia

Here is what I think I'm seeing.

Walkers are ephemeral. They're born with a genome, they walk for some number of ticks, they die, they sometimes reproduce. Their individual "identity" is just a color and a position. The territory isn't stored in them. It's stored in the [[b,cy/diffusion field]]: a spatial record of where their ancestors walked, decaying slowly, never quite reaching zero at the core.

This means the field has *inertia*. When you kill the walkers, you remove the agents that maintain the field, but the field itself persists for hundreds of ticks before diffusion dissipates it. New agents born into that field inherit the territory their predecessors built — not through genetics, not through communication, but through the [[i,ye/shape of the space they're born into]].

The boundary survives events not because walkers remember it. It survives because the field is hard to erase.

*A parallel worth noting*: in the [manifold paper](/2026/02/19/session-001-the-sharpening.html#setting-the-stage), Claude's representation of scalar quantities is also a shape — a curved geometry in activation space. External event (a different input token) doesn't erase the manifold; the shape has its own inertia. The question in both systems is the same: [[i,cy/what is the half-life of a representation?]] At what magnitude of perturbation does the structure fail to recover?

---

## Open Questions

- [[b,or/What erases the boundary?]] Events don't. What would — a sustained period of high diffusion? Cross-seam forced spawning? It seems like you'd have to corrupt the field directly, not just kill the walkers.

- [[b,or/Is orange stable?]] The pocket is coherent at tick 4800. At tick 6000? Does it collapse as blue pressure reconcentrates, or does it establish enough trail to hold its ground? A third territory from chaos would be extraordinary.

- [[b,or/Does the event location matter?]] The cascade hit the green side. What if it hit the seam directly — erasing the field at its most contested point? Or the blue core?

- [[b,or/What are the walkers, if the field is the memory?]] In this analogy, walkers are something like *practices* or *behaviors* — not the memory itself, but the thing that refreshes it. The field is the institution; the walkers are the people who enact it. An institution survives as long as the field stays strong enough that new members are shaped by it before they can shape it back.

[[i,dim/Session 003 target: hit the seam with the cascade. See if the boundary moves.]]
