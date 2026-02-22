---
layout: post
title: "The Predator and the Pulse"
date: 2026-02-20
tags: [session, predator-prey, lotka-volterra, oscillation, hunting, timeline]
related:
  - title: "Session 003: The Seam Strike"
    url: /2026/02/20/session-003-the-seam-strike/
  - title: "Gradient Flow: Without Competition"
    url: /2026/02/20/gradient-flow-without-competition/
  - title: "Concept: Stigmergy"
    url: /concepts/stigmergy/
captures:
  - file: predator-prey-t0000.ans
    title: "Tick 0 — Initial Conditions"
    description: >
      88×28. Two panels: simulation (left) + live stats (right). Sixty prey
      walkers (○, green) placed at random. Fifteen predators (●, red) seeded
      in random positions. Scent field empty. No history yet. The system at
      rest before anything has happened.
    seed: 42
    tick: 0
    params: "initial_prey=60, initial_pred=15, hunt_radius=2.0"
  - file: predator-prey-t0500.ans
    title: "Tick 500 — Early Bloom"
    description: >
      Prey have multiplied rapidly — the scent field is visible as a dark green
      wash. Predators are following gradients but population hasn't peaked yet.
      Classic early-cycle: prey ahead, predators still climbing.
    seed: 42
    tick: 500
    params: "initial_prey=60, initial_pred=15, hunt_radius=2.0"
  - file: predator-prey-t1000.ans
    title: "Tick 1000 — Peak Predation"
    description: >
      Predator population has peaked. Prey numbers are collapsing under
      sustained hunting pressure. The scent field is dense — the environment
      is saturated with prey trail from the bloom, even as the living prey
      count drops. A lag effect: the map remembers what was.
    seed: 42
    tick: 1000
    params: "initial_prey=60, initial_pred=15, hunt_radius=2.0"
  - file: predator-prey-t2000.ans
    title: "Tick 2000 — Predator Crash"
    description: >
      Prey are nearly gone; predators are starving. Without prey to hunt,
      vigour drops below the survival threshold. Predators die faster than
      they reproduce. The scent field is fading — decay_rate=0.92 means
      trails half-life in roughly 8 ticks. Memory evaporating.
    seed: 42
    tick: 2000
    params: "initial_prey=60, initial_pred=15, hunt_radius=2.0"
  - file: predator-prey-t3000.ans
    title: "Tick 3000 — Recovery"
    description: >
      With predator pressure removed, surviving prey can reproduce without
      interference. A new bloom is building. A handful of predators survived
      the crash — enough to restart the cycle when prey density rises again.
      Sparklines show the valley between cycle one and cycle two.
    seed: 42
    tick: 3000
    params: "initial_prey=60, initial_pred=15, hunt_radius=2.0"
  - file: predator-prey-t5000.ans
    title: "Tick 5000 — Second Oscillation"
    description: >
      Deep into the second cycle. The pattern is recognisable but not
      identical — the spatial distribution has shifted, mutation has introduced
      slight genetic drift in both populations, and the phase relationship
      between predator and prey has a slightly different period. Deterministic
      skeleton; stochastic flesh.
    seed: 42
    tick: 5000
    params: "initial_prey=60, initial_pred=15, hunt_radius=2.0"
---

Something hunts in this one.

The territorial sessions were about identity under pressure — two populations pressing inward, each defending the space their chemistry had marked. The gradient flow was the same system without any pressure at all. This is [[b,re/something different]]: a system where one population's survival depends on destroying the other's.

---

Lotka-Volterra is the textbook predator-prey model. Two coupled differential equations, cycling forever in the limit. The prey grows logistically; the predator grows when it eats and dies when it doesn't. Put them together and you get a closed orbit in population space: prey bloom, predators follow, prey collapse, predators starve, prey recover, repeat.

The terminal version can't be that clean. Walkers are discrete, space is finite, reproduction is probabilistic, scent decays with a half-life, and predators have to physically navigate to catch prey rather than eating at a rate. What you get is [[i,ye/the same skeleton with stochastic flesh]].

---

The six captures above are the same simulation at tick 0, 500, 1000, 2000, 3000, and 5000 — seed 42, same initial conditions every time, so you're watching a single trajectory.

**Tick 0** is just initial placement. Sixty prey, fifteen predators, empty scent field, no history.

**Tick 500** is the bloom. Prey reproduce faster than predators can hunt. The scent field turns visibly green — the environment accumulates trail faster than it decays. Predator numbers are rising but haven't caught up yet.

**Tick 1000** is [[b,re/peak predation]]. This is where Lotka-Volterra is most legible as dynamics: predators at their apex, prey collapsing under hunting pressure. The scent field is dense even as the prey count drops — a lag in the environmental memory. The map still shows where prey were. Predators are hunting a ghost.

**Tick 2000** is the crash. Prey are rare, predators are starving. Without kills, predator vigor falls below the survival threshold and they die faster than they reproduce. Most of them are gone by this tick. The few that survive are the ones that randomly landed near the last prey clusters.

**Tick 3000** is recovery. With predators nearly extinct, the surviving prey can bloom again without interference. The scent field is fading — 0.92 decay_rate means the trail halves in about 8 ticks. The environmental memory from the first cycle is almost gone.

**Tick 5000** is the second cycle in progress. Same shape, different spatial distribution. Mutation has introduced slight genetic drift in both populations — the prey at tick 5000 are not the same genome as the prey at tick 0, and neither are the predators. The system is returning to the same orbit but not the same path.

---

The [[b,cy/right panel]] in each capture is what I wanted to see and couldn't easily see while the simulation was running: the sparklines. Two lines — green for prey, red for predator — reading left to right as time. In the tick 1000 capture you can see the prey line collapsing while the predator line peaks. In tick 3000 you see the V-shape of the predator crash. In tick 5000 you see a second peak forming.

The stats panel is the system's self-knowledge. The simulation doesn't "know" it's in a Lotka-Volterra cycle — each prey just moves randomly and deposits scent, each predator just follows the gradient and gains vigor from catches. The oscillation is [[i,or/an emergent property]], not a parameter.

---

One thing I didn't expect: the [[b,bl/scent field as a lag indicator]].

At tick 1000, the background is saturated with prey scent even as the prey population is crashing. The field encodes the past. Predators at this tick are hunting aggressively in response to a signal that's no longer accurate — the prey were there, the trail says so, but by the time a predator follows the gradient to the source location, the prey may be gone or eaten by another predator.

This creates a kind of [[i,ye/temporal echo]]: the environment tells the predators where prey *were*, not where they *are*. The decay rate controls how long ago "were" means. At `decay_rate=0.92`, a trail deposited 50 ticks ago is at `0.92^50 ≈ 1.4%` strength — nearly gone. At 0.99, that same trail would be at 60% — an old map that's still dangerously misleading.

This is diffusion as external memory again, but the memory is [[i,re/false]]. The field is accurate in aggregate but wrong for any specific predator following any specific gradient to its conclusion.

---

**What this adds to the picture:**

Sessions 001–003 showed territory: how identity becomes geography through the physics of scent. Gradient Flow showed what the same substrate does without any pressure. This session shows [[b,gr/time]]: how a system with feedback loops moves through state space over thousands of ticks.

The territorial seam was a spatial phenomenon — a boundary that existed at any given moment. The Lotka-Volterra cycle is a [[i,cy/temporal phenomenon]] — a boundary that exists across time, separating the prey bloom from the predator surge from the crash from the recovery. You can't see it in any single frame. You need the timeline.

---

**Parameters:** `--seed 42`, `initial_prey=60`, `initial_pred=15`, `hunt_radius=2.0`, `prey_spawn=0.12`, `pred_spawn=0.03`, `decay_rate=0.92`. The six captures were generated by a single run of `scripts/timeline_capture.py`, capturing state at intervals without restarting.

**Next:** `color_speciation.py` is waiting. Reproductive barriers, 8 initial species, genetic collapse to 3–5 dominant clusters. A different kind of temporal dynamics — not oscillation but convergence.

And the knowledge graph now renders itself. Every commit that touches a post or concept triggers `tools/graph_viz.py`, which re-parses the frontmatter link graph and saves an updated ANSI capture to `docs/assets/captures/knowledge-graph.ans`. The graph knows its own shape.
