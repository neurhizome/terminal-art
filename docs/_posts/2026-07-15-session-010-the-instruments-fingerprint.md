---
layout: post
title: "Session 010: The Instrument's Fingerprint"
date: 2026-07-15
tags: [session, lens, jlens, calibration, white-noise, cross-instrument, registers]
related:
  - title: "Session 009: The Medium Refuses"
    url: /2026/07/14/session-009-the-medium-refuses.html
  - title: "Session 008: The Arithmetic of Aliveness"
    url: /2026/02/25/session-008-the-arithmetic-of-aliveness.html
captures:
  - file: blog-instrument-fingerprint.ans
    title: "White light through 33 transports — 100 random directions × 33 layers"
    description: >
      The same 100 random unit vectors (residual-space white light — no
      text, no mind) decoded through every layer's J-lens transport for
      gemma4-e2b. One row per layer, one column per direction; glyph and
      color are the decoded top-1 token, so identical decodes form
      visible runs. Right margin: transport effective rank (of 1536) and
      the count of distinct "voices" among 100 decodes. ◦ marks layers
      the new calibration flags as low-rank.
    params: "cols=100, seed=1536, source=instrument_fingerprint.py"
---

Every other session in this blog hunts for order emerging from noise and
celebrates finding it. This one inverts the aesthetic: the input is pure
noise — 100 random unit vectors, the white light of residual space, with
no text and no mind behind them — and **any order in the output is an
artifact of the instrument.** The J-lens calibration work in homelab/lens
(2026-07-15) found that the mean-Jacobian transports for layers 6–12
collapse to effective rank 13–29 of 1536. This piece asks what that
collapse looks like.

## What was predicted

Stripes at the flagged band. Rank 13 means thirteen surviving directions;
I expected L8's row to collapse into runs of the same few tokens — the
'Three'/'2' monoculture the crystalline weaves showed — with confetti
above and below.

## What happened

The stripes are real but they are **not where the rank collapse is.**

| band | eff-rank | voices per 100 | texture |
|---|---|---|---|
| L1–L4 | 57–77 | 50–82 | `2`/`T` monoculture — the number cluster |
| L6–L12 ◦ | 13–29 | 85–94 | diverse glyphs, *thirteen-dimensional* geometry |
| L14–L22 | 47–77 | 68–77 | almost pure punctuation: `. : ) ! / ;` |
| L24–L33 | 371–1033 | 96–100 | true confetti; L30–32 hit 100/100 |

The flagged band stays confetti in *identity* while being degenerate in
*geometry*. A rank-13 transport still mixes thirteen amplified directions
differently for every random input, and thirteen dimensions is plenty to
reach ninety distinct nearest-tokens. Meanwhile the shallow layers, at
four times the rank, funnel a third of all random space onto a single
token (`2`). **Effective rank measures dimensionality; monoculture is
about how the surviving spectrum aligns with the vocabulary.** Two
different pathologies, and the eye catches the second one.

The middle band is the quiet surprise: L14–L22 decodes white noise as
almost nothing but punctuation — the same register the weave study saw as
"hedges and procedural formality" on real text. The instrument doesn't
just have a fingerprint; it has *registers*, banded by depth: numbers
shallow, punctuation mid, multilingual confetti deep. When a specimen
shows punctuation at L17, some of that was going to be there whatever
Gemma thought.

## Why this matters beyond the pretty wall

Session 009 learned that friend.py's medium refuses to die; the divisor
interval was two flavors of aliveness. Today's lesson is the mirror image
for the lens: **the instrument refuses to go silent.** Feed it nothing
and it speaks in registers. Every lens reading is (model × instrument),
and now both factors have been imaged separately — the calibration JSON
gives the numbers, this wall gives the faces.

## Open

- Decode the thirteen surviving singular directions of L8 *individually*
  and name them — are they the emoji/persona/formatting axes the weave
  hinted at?
- Re-render after flux-018's prose-corpus refit: does the number
  monoculture at L1–4 follow the fit corpus out the door?
- The voices count is a scalar per layer that took one minute to compute
  and caught a structure eff-rank missed. Candidate for the calibration
  JSON alongside eff_rank/top_sv.

*Experiment: `experiments/instrument_fingerprint.py` · capture:
`docs/assets/captures/blog-instrument-fingerprint.ans` · lens calibration:
`homelab/lens/calibration.py`*
