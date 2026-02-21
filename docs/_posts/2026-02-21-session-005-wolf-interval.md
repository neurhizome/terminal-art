---
layout: post
title: "Session 005: Wolf Interval"
date: 2026-02-21
tags: [session, tuning, pythagorean-comma, temperament, music-theory, comma-drift, emergence]
related:
  - title: "Session 005: Mathematical Forms"
    url: /2026/02/21/session-005-mathematical-forms.html
  - title: "The Predator and the Pulse"
    url: /2026/02/20/the-predator-and-the-pulse.html
  - title: "Session 004: The Dissolution"
    url: /2026/02/20/session-004-the-dissolution.html
  - title: "Concept: Diffusion as External Memory"
    url: /concepts/diffusion-memory/
  - title: "Concept: Stigmergy"
    url: /concepts/stigmergy/
captures:
  - file: wolf-interval-t0000.ans
    title: "Tick 0 — Full Chromatic Wheel"
    description: >
      200 walkers seeded at uniform hue spacing across [0, 1). The HSV
      wheel is fully populated — every semitone occupied. Resonance field
      empty. The comma has not yet begun to accumulate. This is the system
      at perfect, temporary equilibrium before the first fifth-seeking step.
    seed: 17
    tick: 0
    params: "walkers=200, tune_rate=0.0008, et_tick=500"
  - file: wolf-interval-t0500.ans
    title: "Tick 500 — EqualTemperament Fires"
    description: >
      Just before and just after tick 500 are two different universes.
      Before: the hue distribution has already begun to drift — a careful
      eye sees the population shifted roughly 4° around the wheel from its
      starting position. After: all 200 walkers snap to nearest semitone.
      The resonance field carries the memory of 500 ticks of fifth-seeking;
      the genome state carries none of it. The comma restarts from zero.
    seed: 17
    tick: 500
    params: "walkers=200, tune_rate=0.0008, et_tick=500"
  - file: wolf-interval-t1200.ans
    title: "Tick 1200 — The Wolf Shadow Appears"
    description: >
      A gap in the color population. One hue band — roughly 1/12 of the
      wheel — has significantly fewer walkers than any other. No code
      produced this. The comma accumulated, the population drifted, and the
      geometry of twelve fifth-steps refusing to close an octave carved out
      a void. The wolf fifth is not a rule. It is a consequence.
    seed: 17
    tick: 1200
    params: "walkers=200, tune_rate=0.0008, et_tick=500"
  - file: wolf-interval-t3000.ans
    title: "Tick 3000 — Two Schools"
    description: >
      The population has cleaved into two tuning schools orbiting the wolf
      gap from opposite sides. Status line reads: WOLF bin=7 [18%]. The
      resonance scent field shows twelve hot nodes connected in an arc —
      the circle of fifths, drawn on the terminal floor by the walkers'
      own meeting patterns, with a break where the wolf sits.
    seed: 17
    tick: 3000
    params: "walkers=200, tune_rate=0.0008, et_tick=500"
---

The keyboard was invented to hide a wound.

---

Not metaphorically. Literally. The wound has a name — the [[b,or/Pythagorean comma]] — and keyboard makers have been concealing it for five hundred years. Here is what it is:

Tune a string to C. Tune another string to the perfect fifth above that: G. The perfect fifth has frequency ratio 3:2 — the simplest possible harmonic relationship after the octave. Now keep going. G → D → A → E → B → F♯ → C♯ → G♯ → D♯ → A♯ → F → C. Twelve steps of pure fifths, and you're back where you started.

Except you're not. You are [[b,ye/23.46 cents sharp]] of where you started. That gap — smaller than a quarter of a semitone, too small to hear in isolation, absolutely devastating in ensemble — is the Pythagorean comma. It is not a mistake. It is a geometric truth. Twelve pure fifths and seven pure octaves are incommensurable. No ratio of integers makes them equal. The circle of fifths is not actually a circle. It is a [[i,or/helix that refuses to close]].

What keyboard makers did was hide the wound by distributing the comma across all twelve fifths equally — equal temperament. Every interval becomes slightly wrong in the same direction. The wolf fifth (the brutal dissonant one you'd hear if you *didn't* distribute it) gets tamed. The keyboard sounds nearly right in all keys instead of perfectly right in some and howling in one.

Tonight I asked: what does the comma look like when you can see it accumulate in real time?

---

## The Experiment

Two additions to the toolkit for this session. The [[b,cy/`Genome`]] class receives a new method, `tune_toward`, which nudges `color_h` fractionally toward the Pythagorean fifth above a partner's hue:

```python
PYTHAGOREAN_FIFTH = math.log2(1.5)   # ≈ 0.58496…

def tune_toward(self, other, rate=0.0008):
    target = (PYTHAGOREAN_FIFTH + other.color_h) % 1.0
    self.color_h = circular_mean(
        [self.color_h, target],
        [1.0 - rate, rate]
    )
```

That constant — `math.log2(1.5)` — is the Pythagorean fifth in octave-fraction space. The equal-tempered seventh is `7/12`. The difference is `≈ 0.00163`. [[b,or/That is the comma, per fifth interaction, per walker, per tick.]]

The [[b,cy/`FifthSeek`]] behavior finds the nearest walker whose hue sits approximately one Pythagorean fifth above the current walker's, and moves one step toward it. When two walkers meet at a fifth relationship, both `tune_toward` fires and a [[b,cy/resonance scent]] is deposited at their midpoint — tracing the history of fifth-encounters on the grid floor.

The [[b,bl/`EqualTemperament`]] event (new to `src/events/event.py`) fires at tick 500, snapping every walker's `color_h` to the nearest `k/12` multiple. It is a one-shot event. It resets all the accumulated drift to zero. It does not reset the walkers' [[i,dim/understanding]] of what they're trying to find — that geometry is still encoded in `PYTHAGOREAN_FIFTH`. The drift restarts immediately.

Run it:

```bash
python experiments/wolf_interval.py --walkers 200 --seed 17
```

---

## What I Watched

**Ticks 0–300:** The simulation looks like any other color experiment. Two hundred dots distributed uniformly across the hue spectrum, drifting and clustering. The status line shows `drift +0.0¢` climbing toward `+4.0¢`, `+8.0¢`. You cannot see it in the colors. The drift is in the genome, not the eye.

[[i,dim/This is how the comma works in real instruments too. You can't hear it until it has somewhere to accumulate.]]

**Tick 500:** The [[b,or/`EqualTemperament`]] event fires. Every walker snaps to a chromatic grid position. The resonance field holds its shape — 500 ticks of fifth-meeting history, now pointing to where walkers *were* before the snap. The walkers resume their fifth-seeking from clean semitone positions. The comma restarts. The drift counter resets to `+0.0¢`.

Watch it begin climbing again. [[b,ye/Faster this time.]] The walkers know exactly where their fifths are — the snap has clarified the geometry — and the tuning interactions become more efficient. The second cycle of comma accumulation outpaces the first.

**Tick 800–1200:** Something happens. A gap.

One bin in the hue histogram — `bin=7` tonight, but it varies by seed — starts falling behind. The other eleven bins maintain roughly equal population. This one [[i,or/thins]]. By tick 1200 the status line reads `WOLF bin=7 [18%]`. Eighteen percent of expected population in that hue band.

[[b,re/No code put the wolf there.]] No rule said "avoid bin 7." Every walker just sought its Pythagorean fifth, tuned toward it by a tiny fraction, and the geometry of twelve fifth-steps refusing to close the octave carved out a void. The wolf interval is the shadow of an impossibility.

**Tick 2000–3000:** The population has split into two schools. One group orbits the wolf gap from the sharp side. Another orbits from the flat side. They are drifting in opposite directions — one sharpening, one flattening — because each is seeking its fifth in the direction that avoids the gap. The gap widens. The schools pull apart.

The resonance scent field at tick 3000 shows twelve hot nodes arranged in an arc across the grid. The arc breaks at the wolf. The circle of fifths is [[i,cy/drawing itself on the terminal floor]], with the wound visible as a dim zone where no fifth-meetings happen, because no walker dwells near there long enough to be found.

---

## The Thing That Surprised Me

I expected the hue drift. I designed it.

What I did not expect was [[b,gr/the arc in the resonance field]].

The walkers are not "trying" to draw the circle of fifths. They are each, locally, seeking a partner at approximately `+0.585` hue distance, meeting them, tuning, depositing a scent point, moving on. The scent field simply records where fifth-meetings happened. But because the fifth-relationship has a specific geometry — each meeting point is `0.585` hue distance from the initiating walker — the meetings are not uniformly distributed across the grid. They cluster at positions that are themselves related by fifths.

After 3000 ticks, the scent field has 12 hot nodes. The twelve are arranged in the exact topology of the circle of fifths. Not by design. By [[b,cy/stigmergy]] — the environment accumulating the implicit structure of the walkers' behavior, making it visible to everyone, including the next generation of walkers who will arrive with no history and immediately begin reinforcing the same pattern.

The circle drew itself. The comma made the gap. The terminal just watched and reported.

---

## The Equal Temperament Question

Keyboard makers solved the comma by [[b,dim/not solving it]] — by hiding the wolf, spreading the wound so thin no one wound hears it howl. The EqualTemperament event does the same thing. It snaps everyone to the grid. It temporarily makes every fifth exactly `7/12`. It silences the wolf.

And then the walkers start tuning again, and the comma restarts, and by tick 1500 past the snap you have [[b,re/a second wolf, forming in the same bin it was before]].

Because the comma is not a mistake in the walkers' behavior. It is a consequence of the walkers being physically unable to both (1) use the pure Pythagorean fifth and (2) close the circle. The equal-temperament snap is not a solution. It is a [[i,or/postponement]]. The drift is in the constant `math.log2(1.5)`. You cannot tune it away without changing what a fifth *is*.

---

## Parameters and Code

New code in this session:
- [`src/genetics/genome.py`](https://github.com/neurhizome/terminal-art/blob/main/src/genetics/genome.py) — `Genome.tune_toward()` method
- [`src/automata/behaviors.py`](https://github.com/neurhizome/terminal-art/blob/main/src/automata/behaviors.py) — `FifthSeek` behavior
- [`src/events/event.py`](https://github.com/neurhizome/terminal-art/blob/main/src/events/event.py) — `EqualTemperament` event
- [`experiments/wolf_interval.py`](https://github.com/neurhizome/terminal-art/blob/main/experiments/wolf_interval.py) — the experiment

Session parameters: `--walkers 200 --seed 17 --tune-rate 0.0008 --et-tick 500`. The `tune_rate` controls how fast the comma accumulates. At `0.0008` the drift is slow enough to be legible as gradual rotation. At `0.005` the wolf appears within 200 ticks and the system reaches crisis quickly. At `0.0002` you can run for 10,000 ticks watching imperceptible drift before the gap forms — which is probably the most honest representation of how the comma feels to musicians who've spent careers in equal temperament and barely notice it's there.

---

**What this adds to the picture:**

Sessions 001–004 showed territory, oscillation, and dissolution — systems where the drama is [[i,cy/spatial]]. The comma experiment is different. The drama is [[i,or/pitch-theoretic]]. The color wheel is not just a visual device; it is an octave, and the walkers are genuinely navigating the mathematics of tuning.

The wolf is not a predator. It is not a disaster. It is the [[b,i,or/signature of consistency]]: the mark left on any system that commits to a pure harmonic relationship and refuses to lie about what that means in closed space.

---

*The keyboard was invented to hide a wound. The terminal is not a keyboard.*
