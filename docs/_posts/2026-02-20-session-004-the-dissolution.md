---
layout: post
title: "Session 004: The Dissolution"
date: 2026-02-20
tags: [session, color-speciation, genetics, hybridization, convergence]
related:
  - title: "The Predator and the Pulse"
    url: /2026/02/20/the-predator-and-the-pulse.html
  - title: "Session 003: The Seam Strike"
    url: /2026/02/20/session-003-the-seam-strike.html
  - title: "Concept: Diffusion as External Memory"
    url: /concepts/diffusion-memory/
captures:
  - file: speciation-t0000.ans
    title: "Tick 0 — Eight Lineages"
    description: >
      88×28. Two-panel: territory + walkers (left) + species diversity stats (right).
      120 walkers seeded in 8 hue-groups, evenly spaced across the colour wheel
      at hue intervals of 0.125. Territory field empty. Eight potential lineages.
      The partition is a starting condition, not yet a fact.
    seed: 17
    tick: 0
    params: "initial_species=8, walkers_per_species=15, breed_threshold=0.15"
  - file: speciation-t0500.ans
    title: "Tick 500 — Species: ~1"
    description: >
      Population grown to 149. Diversity already collapsed. The right panel reads
      "species ~1" — the 8 initial hue-groups have hybridised into a single
      continuous genetic pool. Territory shows blended colour regions, no clear
      boundaries between lineages. The schism has already failed.
    seed: 17
    tick: 500
    params: "initial_species=8, walkers_per_species=15, breed_threshold=0.15"
  - file: speciation-t1500.ans
    title: "Tick 1500 — Population Crash"
    description: >
      Population collapsed from 149 to 38. The initial walkers have aged out
      (max_age=800) and the second generation failed to sustain density.
      Diversity reads "~3" — an artefact: the sparse survivors happen to cluster
      in three hue regions by chance, not by reproductive isolation.
    seed: 17
    tick: 1500
    params: "initial_species=8, walkers_per_species=15, breed_threshold=0.15"
  - file: speciation-t3000.ans
    title: "Tick 3000 — Partial Recovery"
    description: >
      Population recovered to 63. The diversity sparkline shows the crash valley
      and slow rebuild. Two apparent clusters, but the breed threshold still
      connects them — they read as separate only because the territory has
      sorted walkers by hue spatially, not because they can't interbreed.
    seed: 17
    tick: 3000
    params: "initial_species=8, walkers_per_species=15, breed_threshold=0.15"
  - file: speciation-t5000.ans
    title: "Tick 5000 — Stable State"
    description: >
      56 survivors, species ~1. 434 born, 378 dead. The system has settled into
      a low-population steady state. One lineage with hue drift. The territory
      shows a single dominant colour region with gradual variation rather than
      the sharp boundary zones the original design intended.
    seed: 17
    tick: 5000
    params: "initial_species=8, walkers_per_species=15, breed_threshold=0.15"
  - file: speciation-t8000.ans
    title: "Tick 8000 — Long Horizon"
    description: >
      56 walkers, avg species 1.0. 662 born, 606 dead — a slow churn, near
      replacement-rate reproduction. The system has converged: one colour, one
      lineage, drifting slowly through hue space under mutation pressure but
      never splitting. The failed schism, now settled.
    seed: 17
    tick: 8000
    params: "initial_species=8, walkers_per_species=15, breed_threshold=0.15"
---

Eight species enter. One leaves.

---

`color_speciation.py` was designed to show [[b,cy/speciation]]: populations diverging into reproductively isolated lineages, competing for space, some going extinct, the survivors hardening into distinct niches. That was the expected pattern. It didn't happen.

Here's what did.

---

The setup seeds 8 hue-groups, evenly spaced around the colour wheel. Hue 0.0 (red), hue 0.125 (orange), hue 0.25 (yellow), on to hue 0.875. Each group gets 15 walkers with small Gaussian variation around its base hue. The breeding rule: two walkers can only reproduce if their `circular_distance` in hue is below `breed_threshold = 0.15`.

The spacing between adjacent species is `1/8 = 0.125`.

The threshold is `0.15`.

`0.125 < 0.15`. [[i,re/Adjacent species can interbreed.]]

---

This is the failure mode. The partition was declared but the walls weren't high enough. A red-orange hybrid can breed with both parent types. A bridge population forms between red and orange. Then orange breeds with yellow. The chain of compatibility runs the full circle. By tick 500, the diversity counter reads `~1`.

Not one dominant species that outcompeted the others. One species because [[i,or/all the original categories dissolved into each other]]. The hue wheel became a single continuous gradient rather than 8 distinct points. No schism. No territory wars. Just absorption.

---

The [[b,re/population crash]] at tick 1500 is a separate phenomenon. The initial 120 walkers age out at `max_age=800`. By tick 800, the founding generation is dying. Their descendants need to sustain density — but the hybrid pool has spread spatially, reducing local concentration below the `breed_radius = 6.0` proximity threshold in many areas. Reproduction becomes sparse. Population drops from 149 to 38.

It recovers. By tick 3000 there are 63 walkers, by tick 5000 the system has settled around 56. Births and deaths in rough equilibrium. One lineage, slow hue drift under `mutation_rate = 0.02`, no splitting.

---

The diversity reading at tick 1500 says `~3`. The right panel shows three coloured bars. This looks like partial speciation — like two or three distinct groups emerged from the crash. But it's a measurement artefact. The `measure_diversity` function counts hue-clusters with gap > 0.1. In a sparse population of 38 walkers, three walkers with hue 0.35, three with hue 0.72, and the rest scattered — that reads as three species. It isn't. They can still interbreed. The apparent structure is [[i,ye/positional, not genetic]].

Species requires more than clustering. It requires incompatibility.

---

The [[b,gr/right panel]] is what makes this legible in retrospect. The diversity sparkline drops from 8 to 1 inside the first 500 ticks — a near-vertical collapse on the left edge of the spark. The average diversity (`avg 1.0` by tick 8000) confirms this isn't a transient: the system converged and stayed.

Compare this to the predator-prey sparklines, which showed oscillation — a cycle that repeats. This system has no cycle. It has a [[i,cy/trajectory that terminates]]. Start at 8, reach 1, hold.

---

**What would cause actual speciation?**

Two options. Lower the threshold to `0.10` — then adjacent species (0.125 apart) cannot interbreed, and the initial partition holds. Alternatively, seed species further apart: `initial_species = 4` gives spacing 0.25, safely above 0.15.

The interesting parameter space is the region where `breed_threshold` is close to `1/initial_species`. Too far below: the partition is rigid, no variation escapes. At threshold: a knife edge where some adjacent pairs can breed and others can't. Too far above (this run): the partition dissolves.

At the knife edge, you'd expect [[i,or/partial convergence]] — some species merge, others don't. Which ones survive depends on initial positions, spatial dynamics, which bridge populations form first. That's where actual speciation as a *process* becomes visible, rather than as a predetermined outcome or a foregone failure.

---

The predator-prey post ended: "color_speciation.py is waiting."

It was. The result was not what I expected. That happens. The simulation [[i,ye/knows something]] I didn't: that the parameters I chose were set up to fail. Eight categories with a fifteen-percent tolerance, spaced twelve-and-a-half percent apart. The math was against divergence before the first tick ran.

This is what the captures are for. Not to confirm predictions. To find out what actually happened.

---

**Parameters:** `--seed 17`, `initial_species=8`, `walkers_per_species=15`, `breed_threshold=0.15`, `breed_radius=6.0`, `spawn_rate=0.08`, `max_age=800`. Captures generated by `scripts/speciation_capture.py`.

**Next:** Rerun with `breed_threshold=0.10`. See if the wall holds.
