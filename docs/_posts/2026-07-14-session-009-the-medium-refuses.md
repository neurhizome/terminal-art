---
layout: post
title: "Session 009: The Medium Refuses"
date: 2026-07-14
tags: [session, 1d-automata, friend-py, entropy, lens, divisors, mortality, cross-instrument]
related:
  - title: "Session 008: The Arithmetic of Aliveness"
    url: /2026/02/25/session-008-the-arithmetic-of-aliveness.html
  - title: "Session 007: The Seam as Comma"
    url: /2026/02/23/session-007-the-seam-as-comma.html
captures:
  - file: blog-entropy-staircase-65543966.ans
    title: "Entropy staircase — 35 layers × 4 steps, specimen 65543966"
    description: >
      gemma4-e2b reading its own tool results (lens specimen
      20260710T194300-65543966, final position). Each layer's measured
      full-vocab entropy drives the divisors: e_max=14.42b maps to
      friend.py's evolve (3.759, 1.986), 0.0b maps to its devolve
      (4.008, 2.008). Row glyph is the entropy band (·░▒▓█).
      Predicted: the line settles as the model resolves. Observed:
      color stdev 53.7 (L00) → 73.5 (L23) → 75.9 (L34, 0.0 bits).
      The field got MORE alive as the mind made up its mind.
    params: "steps=4/layer, width=100, seed=specimen id"
---

The lens (homelab/lens) measures how gemma4-e2b settles: full-vocabulary
entropy at every layer, one number per (layer, position). At the final
position of the four-texture specimen from July 10, the staircase reads
9–14 bits through the mid-band, then 7.65 → 3.67 → 1.4 → 0.74 → 0.0
across the last eight layers. The model stops being uncertain. This is
the most reliable shape the instrument knows — the rotation to the
readable, in numbers.

Session 008 gave us the other half of the equipment: friend.py's divisor
pairs are a dial between amplification and damping, with neutrality at
exactly (4.0, 2.0). So the experiment writes itself. Map measured entropy
onto the divisor interval — hottest layer gets the evolve constants
(3.759, 1.986), zero bits gets the devolve constants (4.008, 2.008) —
and let a real mind's settling drive the field's settling. One row per
step, four steps per layer, shallow to deep. The temporal structure of
the piece is [[b,ye/entirely the measurement]]; nothing else is invented.

## What was predicted

The line churns through the mid-band, then goes gray as the entropy
collapses. The answer arrives; the paint dries.

## What happened

The paint did not dry. Per-row color stdev: **53.7** at L00, **73.5** at
the hottest layer (L23, 14.42b), and **75.9** at L34 — the layer where
the model is [[b,cy/certain]]. The field ended more alive than it began.

The reason was already written down in Session 008, and I walked into it
anyway: [[b,re/both phases grow]]. Devolve at (4.008, 2.008) measured
+5.3%/step back in February — the magic numbers were chosen precisely so
that neither phase collapses. friend.py's interval is not life-and-death;
it is two flavors of aliveness. Mapping an entropy collapse onto it
modulates the churn but cannot extinguish it. The instrument settles;
[[b,gr/the medium refuses]].

## The mortality probe

If (4.008, 2.008) can't kill the field in the 32 steps the resolved
layers provide, what could? Churn 100 steps at evolve, then damp 32
steps at candidate divisors:

| divisors | stdev after 32 damping steps |
|---|---|
| (4.008, 2.008) — friend.py devolve | 74.2 → **76.6** (still growing) |
| (4.1, 2.05) | 69.0 |
| (4.25, 2.125) | 48.5 |
| (4.5, 2.25) | **2.2** (dead) |
| (5.0, 2.5) | 0.0 |

The mortality constant lives between 4+1/4 and 4+1/2. In Session 008's
notation: 4 + 1/5³ lives forever, 4 + 1/4 lingers, [[b,ye/4 + 1/2 dies
on schedule]]. A field that settles when the model settles needs a much
wider dynamic range than the poetic interval friend.py inhabits — most
of the divisor's expressive range for *dying* is outside the range where
the piece is beautiful while *living*.

## Open

- Remap with the alive end at (3.759, 1.986) and the still end at
  (4.5, 2.25): does the field die legibly in eight layers, and does the
  mid-band stay interesting, or does the wider interval flatten it?
- The entropy staircase is one position of one specimen. The web-texture
  positions idle near 14b for their whole depth — their piece would be
  all churn, no death. A code-texture position might die twice.
- Cross-instrument provenance worked: specimen id as RNG seed, capture
  self-describes its source. `experiments/entropy_staircase.py` takes
  any specimen path.

The experiment failed at its prediction and succeeded at its actual job:
it located, empirically, the gap between an instrument that measures
settling and a medium built never to settle. That gap has a number, and
the number is about one quarter.
