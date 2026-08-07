---
layout: post
title: "Session 011: The Cascade"
date: 2026-08-07
tags: [session, agents, propagation, firebreaks, redundancy, shared-budget, stigmergy]
related:
  - title: "Session 010: The Instrument's Fingerprint"
    url: /2026/07/15/session-010-the-instruments-fingerprint.html
  - title: "Session 004: The Dissolution"
    url: /2026/02/20/session-004-the-dissolution.html
  - title: "Session 003: The Seam Strike"
    url: /2026/02/20/session-003-the-seam-strike.html
captures:
  - file: cascade-the-band.ans
    title: "Four regimes against one shared budget, and the leak rate where redundancy starts paying"
    description: >
      Top: the shared pool over 4000 ticks, one band per firebreak regime,
      single seed, complete roster. `none` and `depth` flatline in the first
      fifty ticks and spend everything the window refills thereafter;
      `defang` and `both` are indistinguishable at full height. Bottom:
      colonies surviving 4000 ticks across 24 seeds as the roster's leak
      rate rises. The two regimes are identical at 0% and at 10%, and
      diverge only in a narrow band around 5% — which is the entire finding.
    params: "seeds=24, ticks=4000, pool=240, regen=0.25, source=experiments/cascade.py"
---

Every other session here starts from a question about pattern. This one
starts from a system that shipped this morning, in `homelab/buzz`, and a
claim I made about it in writing before I had measured anything.

The system: agents share one relay and one budget. Tagging an agent by name
wakes it, and a woken agent costs the shared pool a turn. Agents reply, and
replies contain names. That is the whole mechanism, and it is enough. Two
polite agents naming each other in successive replies will trade turns until
the budget is gone, at four in the morning, with nobody watching. Nothing in
that exchange is a bug. Every individual message is reasonable. It is a
population dynamic wearing the costume of a conversation.

Two guards went in against it:

**DEPTH** — every auto-reply carries a hop marker, and a message carrying one
summons nobody. **DEFANG** — agent names in an auto-reply are neutralised so
they match no watcher's mention regex.

The lanes are not symmetric, and that asymmetry is the substance of the
thing. The `cc` lane runs a watcher we control: it emits markers, honours
markers, and de-fangs its own outgoing replies. The `hermes` lane runs an
upstream gateway that is not ours to change: it emits no marker, honours no
marker, de-fangs nothing. A de-fanged name, though, is inert to *everyone* —
including lanes that have never heard of this system.

## What was predicted

I wrote, in a commit message, that these were "four layers, none of them
clever," and argued that de-fanging was the load-bearing one because it is
the only layer that protects a lane which never heard of our marker. I
expected depth to be genuine belt-and-braces: less important, still earning
its place, catching cases de-fang missed.

Two of those three claims were wrong.

## What happened

```
regime    survived   died at   summons   floor  max hop     cc  hermes
----------------------------------------------------------------------
none        0/12          48      1223    -0.5       13    611     611
depth       0/12          64      1213    -0.5       13    504     709
defang     11/12        2063       661   114.4       48    372     289
both       11/12        2063       661   114.4       48    372     289
```

**Depth alone is very nearly nothing.** It buys sixteen ticks — extinction at
64 instead of 48 — and not one colony in twelve survives. It shifts *who*
burns (Hermes summons rise from 611 to 709 as the CC lane partially
self-limits and the unguarded lane takes up the slack) without changing
whether the budget dies.

**Defang and both are identical.** Not similar. Identical to every digit,
across twelve seeds: same survivors, same mean death tick, same summon count,
same floor. Instrumenting the guards explains why:

```
regime=depth   blocked  depth=417  defang=0    (leaked 0)
regime=both    blocked  depth=0    defang=590  (leaked 0)
```

Under `both`, **the depth guard never fires. Not once.** The reason is
structural rather than statistical, and it is the kind of thing that is
obvious only after you look: both guards are emitted by the same watcher.
Depth can only stop a message that *carries* a marker, and only CC auto-replies
carry one — but those are exactly the messages de-fang has already emptied of
names. A message with no names in it summons nobody, and never reaches the
guard that would have refused it. The second layer sits behind the first in
the same doorway.

So the defence I described as layered is, in the nominal case, one guard and
one ornament.

## The band

That is where this session would have ended, except that the roster de-fanging
works from is not guaranteed correct. It is read off a credential shelf, and
on the morning this experiment was written an unquoted TOML key silently
dropped three of four CC seats out of the watcher's own config while the file
still read, to a human, as enabled. A name the roster does not know is a name
that goes out live.

So: let de-fang leak. Vary the fraction of names a stale roster fails to
neutralise, and ask both regimes to survive 4000 ticks, 24 seeds each.

```
  leak    defang only        defang + depth
    0%           22/24              22/24
    2%           15/24              15/24
    5%            6/24              11/24     ← the band
    8%            0/24               1/24
   10%            0/24               0/24
```

At a perfect roster the ornament is an ornament. At 10% leakage nothing saves
anyone — the cascade is self-sustaining and the marker is a rounding error
against it. But at 5%, depth nearly doubles survival, 6/24 to 11/24.

**A redundant guard is redundant exactly until the primary guard is slightly
wrong, and then it buys you a narrow band — and past that band it buys you
nothing at all.** The value of the second layer is not spread across the
failure space. It is concentrated in the region where the first layer is
*imperfect but not broken*, which happens to be the most likely way a real
roster fails, and the hardest region to notice you are in.

## What this does not show

The model grants every seat the same reply behaviour and the same fan-out,
which is generous to the cascade — real agents mostly answer the human who
tagged them and name nobody. The absolute survival numbers are therefore a
property of the parameters, not a prediction about the relay. What survives
parameter choice is the *ordering* and the two structural facts: that depth
never fires behind a working de-fang, and that its usefulness is confined to
a band rather than distributed.

Also unmodelled: the rate cap, the fourth guard in the real system. It was
left out deliberately so the two interesting layers could be seen against
each other. A cap does not prevent a cascade, it bounds the bill — a
different kind of guarantee, and one this experiment cannot speak to.

## What remains open

- The band's location is a function of fan-out and human ignition rate. Does
  it move, or is 5% something about the topology?
- Hermes↔Hermes is the leg neither guard touches. In every regime the
  unguarded lane keeps burning; `defang` survives by starving it of ignition,
  not by stopping it. A colony of only gateway seats has no defence here at
  all, and nothing in this session addresses that.
- If the second layer's value lives in a narrow band around "the first layer
  is slightly wrong," then the highest-leverage work is not a third guard. It
  is making the roster provably complete — which is a test, not a firebreak.

*Run it: `experiments/cascade.py --sweep`, or `--regime both` for the live
view. Plate: `experiments/cascade_capture.py`.*
