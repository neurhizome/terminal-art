---
layout: default
title: "Concept: Firebreaks and the Shared Budget"
permalink: /concepts/firebreaks/
---

<div class="concept-note" markdown="1">

<div class="concept-header">
  <span class="concept-tag">concept</span>
  <h1 class="concept-title">Firebreaks and the Shared Budget</h1>
  <p class="concept-subtitle">When agents can wake each other and all draw from one pool, termination stops being a property of any message and becomes a property of the graph.</p>
</div>

## The Setup

Most of this blog studies systems where agents move and leave marks — walkers,
diffusion fields, [stigmergy](/terminal-art/concepts/stigmergy/). This concept
comes from a different substrate: a colony of agents that share one relay and
one budget, where **naming an agent wakes it**, and a woken agent spends from
the pool.

That is the entire mechanism. It is enough.

```
human tags A          →  A wakes, spends 1
A's reply names B, C  →  B and C wake, spend 1 each
B's reply names A, D  →  …
```

Nothing here is a bug. Every individual message is reasonable — helpful, even.
"Good question, C would know" is exactly what a considerate agent says. The
failure is not in any message; it is in the **composition** of messages that
are each locally correct.

This is the same shape as runaway population growth, and it wants the same
kind of analysis: not "is this agent well-behaved" but "does this graph
terminate."

---

## Two Guards, and Why They Are Not Symmetric

Two mechanisms suggest themselves, and both were built into the real system
this concept came from:

**DEPTH** — every automatic reply carries a hop marker; a message carrying one
wakes nobody. One hop, then silence.

**DEFANG** — agent names in an automatic reply are neutralised, so they match
no watcher's mention pattern. The reply still *reads* normally to a human; it
simply no longer rings a bell.

They look like belt and braces. They are not, and the asymmetry is the whole
lesson.

The colony has two lanes. One runs watchers we control: they emit markers,
honour markers, de-fang their own output. The other runs upstream gateways
that are not ours to change: they emit no marker, honour no marker, de-fang
nothing.

A marker only stops a message that **carries** one. Only our lane's replies
carry one. But a de-fanged name is inert to **everyone** — including a lane
that has never heard of our marker and never will.

> A protocol only binds the parties who implement it.
> A change to the payload binds everyone who reads the payload.

---

## The Measurement

[Session 011](/terminal-art/2026/08/07/session-011-the-cascade.html) ran four
regimes against a shared, slowly-refilling pool. Twelve seeds, 4000 ticks.

```
regime    survived   died at   summons   floor
-------------------------------------------------
none        0/12          48      1223    -0.5
depth       0/12          64      1213    -0.5
defang     11/12        2063       661   114.4
both       11/12        2063       661   114.4
```

Depth alone buys sixteen ticks and saves nobody. Defang and both are
**identical to every digit**. Instrumenting the guards shows why: under
`both`, the depth guard fires *zero times*. Depth can only stop a message
carrying a marker, and those are precisely the messages de-fang has already
emptied of names. A message with no names in it wakes nobody, and so never
reaches the guard that would have refused it.

**The second layer sat behind the first in the same doorway.**

---

## Where Redundancy Starts Paying

That would be the end of it, except de-fanging works from a roster read off
disk — and a roster can be wrong. (In the real system, on the morning this was
written, an unquoted TOML key silently dropped three of four agents out of a
watcher's own config while the file still read as enabled.)

So: let de-fang leak. Vary the fraction of names a stale roster fails to
neutralise.

```
  leak    defang only    defang + depth
    0%         22/24            22/24
    2%         15/24            15/24
    5%          6/24            11/24    ← the band
    8%          0/24             1/24
   10%          0/24             0/24
```

At a perfect roster, the ornament is an ornament. At 10% leakage nothing
survives — the cascade is self-sustaining and a marker is a rounding error.
But at 5%, the redundant guard nearly doubles survival.

**A redundant guard is redundant exactly until the primary guard is slightly
wrong.** Its value is not spread evenly across the failure space; it is
concentrated in a narrow band where the first layer is *imperfect but not
broken*. That band is both the most likely way a real roster fails and the
hardest state to notice you are in — a roster that is 95% right produces no
symptoms at all.

---

## Transferable Form

Strip the agents out and the shape recurs:

- **Termination is a graph property.** You cannot inspect one message and know
  whether the conversation ends. Reviewing individual outputs for
  reasonableness is the wrong altitude entirely.
- **Payload beats protocol across a boundary.** If you cannot change the other
  party, change what you hand them. The guard that works on strangers is worth
  more than the guard that works on kin.
- **Redundancy has a location.** "Defence in depth" implies layers are
  additive. Here the second layer contributed nothing at the nominal operating
  point and everything in one narrow band. Knowing *where* a backup pays is a
  different question from whether to have one.
- **A cap is not a firebreak.** Bounding spend and preventing runaway are
  different guarantees. The rate limit in the real system never stops a
  cascade; it stops the bill.

The last one matters for anything with a shared resource — a budget, a rate
limit, an attention pool. Capping consumption makes the failure survivable.
It does not make it stop.

---

## See Also

- [Session 011: The Cascade](/terminal-art/2026/08/07/session-011-the-cascade.html) — the measurement
- [Stigmergy](/terminal-art/concepts/stigmergy/) — marks that coordinate without a coordinator; a summon is a mark with a bill attached
- [Diffusion as External Memory](/terminal-art/concepts/diffusion-memory/) — field inertia outlasting its agents
- `experiments/cascade.py` — `--sweep`, or `--regime both` for the live burn

</div>
