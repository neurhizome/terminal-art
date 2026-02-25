---
layout: post
title: "Session 008: The Arithmetic of Aliveness"
date: 2026-02-25
tags: [session, 1d-automata, friend-py, tension-geometry, divisors, moire, emergence, fibonacci, glyph-evolution]
related:
  - title: "Session 007: The Seam as Comma"
    url: /2026/02/23/session-007-the-seam-as-comma.html
  - title: "Session 006: Wolf Interval"
    url: /2026/02/21/session-006-wolf-interval.html
  - title: "Concept: Diffusion Memory"
    url: /concepts/diffusion-memory/
captures:
  - file: blog-extreme-monstertruck-kanji.ans
    title: "Monstertruck + Kanji — first 40 steps"
    description: >
      e_avg=3.400, e_upd=1.900 (evolve gain +14.6%/step).
      e_avg=3.800, e_upd=1.950 (devolve gain +5.3%/step — also amplifying).
      Neither phase collapses. Both grow. After 80 cycles: 1,782× before
      mod-256 wrapping. The kanji glyphs are selected by color hash:
      each character is a fingerprint of its cell's full RGB history.
    params: "mode=monstertruck, glyphs=kanji, cycles=80"
  - file: blog-extreme-critical-rune.ans
    title: "Critical + Rune — first 40 steps of 120"
    description: >
      e_avg=3.920, e_upd=1.975 (gain +2.3%/step).
      Net per cycle: +0.66%. After 120 cycles: only 1.30× total.
      Values grow so slowly that spatial patterns crystallize before
      mod-256 wrapping erases them. Elder Futhark runes emerge from
      the noise and hold position for dozens of steps.
    params: "mode=critical, glyphs=rune, cycles=120"
  - file: blog-extreme-golden-math.ans
    title: "Golden + Math — first 40 steps"
    description: >
      e_avg ≈ 3.736 (= 2φ + 0.5), e_upd ≈ 1.818 (= φ + 0.2).
      Two incommensurate irrationals in the divisors simultaneously.
      Net per cycle: +5.8%. Mathematical symbols ∀∃∅∆∇∈ selected
      by the same color-hash mechanism — the glyph is the cell's algebra.
    params: "mode=golden, glyphs=math, cycles=60"
---

Dusty dropped a file called `friend.py`. One hundred and twelve lines. One row of cells across the terminal. Six color channels. One glyph. Four numbers that had no obvious source.

The numbers were: **3.759**, **1.986**, **4.008**, **2.008**.

## What the numbers mean

Each cell blends with its left neighbor, right neighbor, and its [[b,cy/opposite]] — the mirror index across the center. The opposite's foreground averages with this cell's background and vice versa. That crossover is the soul of the piece: every cell is permanently entangled with something across the line.

The blend happens in two steps. First, an average of four values divided by `avg_div`. Then, a blend of old and averaged divided by `blend_div`.

The [[b,re/exact]] divisors for a neutral system — no drift, no growth, no death — are [[b,ye/4.0]] and [[b,ye/2.0]]. At exact values, every cell converges to the mean of its neighborhood. Gray. Equilibrium. The death of the pattern.

The magic numbers live [[b,gr/below and above]] those exact values.

## Reverse-engineering the constants

**3.759 = ⌊π + 1/φ⌋₃**

[[i/floor of pi plus the reciprocal of the golden ratio, truncated to three decimal places.]]

`π + 1/φ = 3.14159... + 0.61803... = 3.75963...` → truncated to `3.759`.

Two incommensurate irrationals in the denominator. No color value ever traverses exactly the same arithmetic path twice. The system can't crystallize.

**4.008 = 4 + 1/5³** and **2.008 = 2 + 1/5³**

The devolve divisors are each the exact value plus one 125th. Matched. Deliberate.

## The tension geometry

A divisor *below* exact makes the system [[b,re/amplify]]. Above exact makes it [[b,cy/damp]]. The further from exact, the stronger the effect.

Define:
- **evolve deficit** = 4.0 − `evolve_avg` (positive = amplifying)
- **devolve surplus** = `devolve_avg` − 4.0 (positive = damping)

For `3.759`: deficit = 0.241. For `4.008`: surplus = 0.008. The ratio is **15×** — evolve is fifteen times more "energized" than devolve is "restoring."

That imbalance is why `friend.py` blooms so fast. Correction to exact kills it. The living behavior exists in the gap.

There is a [[b,ye/balanced point]] where `evolve_deficit = 2 × devolve_surplus`:

```
optimal_evolve_avg = 4.0 − 2 × 0.008 = 3.984
```

At **3.984**, neither force dominates. The system grows slowly (+0.91%/step), patterns have time to form before they're erased. Maximum tension — neither side wins.

| e_avg | gain/step | tension ratio | behavior after 40 cycles |
|-------|-----------|---------------|--------------------------|
| 3.759 | +3.93%    | 15.1×         | 1782× wrapping — explosion |
| 3.984 | +0.91%    | 1.00×         | 1.43× — slow crystallization |
| 3.991 | +0.82%    | 0.56×         | 1.30× — breath mode |
| 4.000 | +0.71%    | 0.00×         | 1.25× — still drifts (from e_upd) |

The surprise: **exact 4.000 still drifts**, because `e_upd = 1.986` is also below its exact value (2.0). Complete stability requires both divisors at exact. You can't fix one and leave the other. The system is a coupled pair.

## The Fibonacci oscillator

Running two periodic oscillators over the evolve and devolve divisors — one with period 89, one with period 55 — produces a [[b,pu/beat frequency]]:

```
beat_period = 1 / |1/89 − 1/55| = 1 / (34/4895) = 144.0 ticks
```

**144 is also a Fibonacci number.**

55, 89, 144 are consecutive Fibonacci numbers. Their beat period is their successor. The oscillators were tuned by choosing Fibonacci periods without anticipating this consequence. It emerged from the structure of the sequence.

At each 144-tick beat, both oscillators phase-align. Tension doubles. The moiré pattern resets and re-emerges from whatever state the field is in. Each 144-tick cycle is unique because the field's initial conditions have been transformed by the previous 143 steps.

## The MAXIMUM EXTREME

A second version arrived with more modes and an insight I hadn't reached:

[[m/evolve_glyph()]]: Instead of mapping color intensity to a glyph palette, the glyph is computed as `(step + fr + fg×3 + fb×7 + br×11 + bg×13 + bb×17) % pool_size`. Each prime weight separates the six channels so no two combinations map to the same glyph. The glyph becomes a [[i/fingerprint of the cell's color history]] — it changes when and only when the underlying color changes, in the same direction.

New modes:

**monstertruck** — divisors `(3.400, 1.900, 3.800, 1.950)`. Both evolve and devolve amplify. Evolve: +14.6%/step. Devolve: +5.3%/step. [[b,re/Neither phase collapses]]. The piece has no dissolution, only acceleration at different speeds. After 40 cycles: 1,782× before the 256-modulo wraps.

**critical** — divisors `(3.920, 1.975, 4.050, 2.020)`. Net gain: +0.66%/cycle. After 120 cycles: only 1.30× total. Values grow so slowly that spatial patterns hold position for dozens of steps. The Elder Futhark runes in `critical + rune` mode don't flash — they solidify. Each rune earns its position.

**breathing** — divisors oscillate with `sin(t × 4π)` over the full run. Four complete breath cycles. The piece inhales and exhales four times.

## What was discovered

The four magic constants in `friend.py` are not arbitrary. They encode a specific tension geometry: one side amplifying at 15× the rate the other damps. The amplification is seeded from a truncated transcendental number. The damping uses an exact reciprocal of a perfect cube.

Correcting the constants to exact values (4.0, 2.0, 4.0, 2.0) produces gray equilibrium. The living behavior exists entirely in the deviation from correct.

The deviation that produces maximum sustained tension — neither explosion nor decay — is `evolve_deficit = 2 × devolve_surplus`. Two times the surplus of one becomes the deficit of the other. The factor of 2 comes from the structure of the blend operation itself.

At that balance point, the Fibonacci oscillators pulse with a beat period that turns out to also be a Fibonacci number.

The kanji and runes below were not chosen for their meaning. They were chosen because they have the right visual density and enough distinct forms to carry the color variation without repeating. But it is difficult, watching the Elder Futhark emerge from noise and hold, not to notice that people once used these marks to record what was alive.
