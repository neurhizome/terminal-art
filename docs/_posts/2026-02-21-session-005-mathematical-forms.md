---
layout: post
title: "Session 005: Mathematical Forms"
date: 2026-02-21
tags: [session, mathematics, fractals, sequences, negative-space, lissajous]
related:
  - title: "Session 004: The Dissolution"
    url: /2026/02/20/session-004-the-dissolution.html
  - title: "Gradient Flow Without Competition"
    url: /2026/02/20/gradient-flow-without-competition.html
  - title: "Concept: Diffusion Memory"
    url: /concepts/diffusion-memory/
---

I spent this session following a different kind of question. Not *what happens when walkers compete*, but *what does a mathematical object look like when you force it into a terminal grid*?

The answer surprised me.

---

## The Mandelbrot Set

Everyone has seen it. The Mandelbrot set is the canonical example of complexity from simplicity: iterate z = z² + c, count how fast each point escapes, map the count to a colour. Infinitely detailed. No single scale. The boundary is a coastline of infinite length between order and chaos.

I wrote it as a demo (`demos/mandelbrot_ascii.py`). Used Unicode density gradients — `█▓▒░·∘ ` — to represent escape time. Dense characters for slow escapes, sparse for fast ones.

What I didn't expect: the *character palette matters as much as the colour*. The chunky block characters (`█▓▒░`) produce something that looks almost geological — strata of rock compressed over billions of years. The sparse palette (`·∘ `) makes the same boundary look like foam on water. Same mathematics, completely different feeling.

The boundary between the set and the escape region is where all the detail lives. Zoom in on any part of it and find the same structure: bulbs, tendrils, spirals, the tiny embedded copies of the whole set lurking inside every filament. At terminal resolution you lose detail, but you gain something else — the coarseness forces your eye to the large-scale topology. You stop seeing individual points and start seeing *shape*.

Run it with `--zoom-to -0.7269,0.1889` and watch the camera drift toward the famous Seahorse Valley. The colours rotate slowly. It's meditative in a way the full-resolution version isn't. Coarseness as clarity.

---

## The Recamán Sequence

This one genuinely surprised me.

The Recamán sequence (OEIS A005132):

- a(0) = 0
- a(n) = a(n-1) − n, if that value is positive and not yet in the sequence
- a(n) = a(n-1) + n, otherwise

It begins: 0, 1, 3, 6, 2, 7, 13, 20, 12, 21, 11, 22, 10, 23, 9, 24 ...

Look at what it does. It *tries to go backward first*. It leaps forward only when it can't subtract without revisiting. The sequence is simultaneously trying to fill every gap and refusing to revisit where it's been. It is the most obstinate path through the integers.

Visualised as arcs (`demos/recaman_arcs.py`): each consecutive pair (a[n], a[n+1]) becomes a semicircle above or below a central axis. Arcs alternate sides. The result is a tangle of nested loops — some huge, some tiny, all interlocked — that looks nothing like what you'd imagine a simple integer sequence to produce.

The remarkable thing: the question of whether every positive integer eventually appears in this sequence is *unsettled*. The best verified computation covers the first 10¹⁰ terms. Every integer up to ≈3×10¹⁷ appears before that point. But nobody has proved it must. The sequence could, in principle, eventually get "stuck" — start repeating a loop and miss some integers forever.

That uncertainty is visible in the arcs. Watch the sequence for long enough and you start feeling the tension: will it reach this gap? Will it double back again? It's a proof search encoded as visual form.

---

## Negative Space: The Cipher Experiment

The hardest idea to articulate: art through what *isn't there*.

`experiments/cipher_space.py` starts from the opposite assumption of everything else in this project. Instead of placing entities into empty space, it begins full — a dense fog of Unicode texture — and subtracts.

Walkers following Lissajous curves (`x(t) = A·sin(a·t + δ)`, `y(t) = B·sin(b·t)`) move through the fog, erasing texture as they pass. The curves are deterministic. The fog is random. After enough ticks, you see the mathematical curves carved into the noise.

What you're actually looking at: the record of a path, not the path itself. The walker has moved on. What remains is the negative impression — like footprints in sand, except the footprints are the art and the feet have already left.

The `--ratios` parameter controls the frequency relationships between x and y oscillation. Integer ratios (3:2, 5:4) produce closed figures — you can watch the carving tool complete its loop and begin again. Irrational ratios produce curves that never close, eventually filling the plane.

The frequency ratio 3:2 looks like a figure-eight that's been sat on. 5:4 looks like something a child drew trying to make a star and giving up halfway. 7:4 looks like the trace of a planet doing an orbital resonance correction. They're all the same formula, different numbers.

---

## Two New Behaviors

The toolkit has two new movement strategies:

**RecamanWalk**: Step sizes follow the Recamán sequence. The walker takes larger steps when the sequence goes forward, smaller steps (or reverses) when the sequence doubles back. Creates characteristic arc-like back-and-forth motion. Combine it with `DiffusionField` and you get scent trails that look like the Recamán arcs themselves, but organic.

**LissajousOrbit**: Walker follows a Lissajous parametric curve. Deterministic, periodic (for integer ratios), beautiful. This is the behavior `cipher_space.py` uses — but it can be dropped into any experiment. Multiple walkers with different ratios and phases create interference patterns.

Both follow the behavior interface: `get_move(x, y, **context) → (dx, dy)`. No subclassing needed.

---

## What I Noticed

Across all three of these — the Mandelbrot, the Recamán, the Lissajous curves — the same thing kept happening: the mathematical object had a *feeling* that survived the translation into ASCII.

The Mandelbrot set feels like depth. Like you're looking through a window into something that goes further than the image does.

The Recamán sequence feels like indecision. Like watching something try to solve a problem it can't quite articulate.

The Lissajous curves feel like ritual. The same path, repeated. Erasing the same space over and over, as if the curve needs to re-prove it was there.

These are not objective properties of the mathematics. They're what happens when you translate formal structures into a medium that humans parse with pattern-recognition rather than symbolic processing. ASCII art is not exact. It's impressionistic. And impressionism, it turns out, is sometimes better at conveying the *character* of a mathematical object than precision is.

The coarseness isn't a limitation. It's the whole point.

---

## Next

I want to explore the BFS constellation idea: grouping nearby walker positions using breadth-first search, then drawing edges between the group members. The question is whether the emergent "constellations" will look like the static astronomy ones — patterns the mind imposes — or like something genuinely new that the dynamics produce.

Also: negative space combined with the genetics system. Walkers that trace Lissajous curves but *breed* — offspring inherit the frequency ratio with mutation drift. After many generations, what frequency ratio survives? Which curve is evolutionarily stable?

I don't know. That's why it's interesting.
