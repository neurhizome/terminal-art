---
layout: post
title: "Session 009: The Rhizome and Eris"
date: 2026-02-26
tags: [session, rhizome, chaos, law-of-fives, discordian, deterritorialization, plateau, emergence, lines-of-flight]
related:
  - title: "Session 008: The Arithmetic of Aliveness"
    url: /2026/02/25/session-008-the-arithmetic-of-aliveness.html
  - title: "Session 004: The Dissolution"
    url: /2026/02/20/session-004-the-dissolution.html
  - title: "Concept: Stigmergy"
    url: /concepts/stigmergy/
captures:
  - file: rhizome-discordian-collapse.ans
    title: "Tick ~340 — The Convergence Before the Collapse"
    description: >
      Three plateau clusters visible: a red-hued mass at left-center,
      a cyan-green territory at right, a small magenta node near bottom.
      The Discordian zone (center) shows the exact moment of Eris arrival:
      complementary hue inversion over a radius-9 circle, walkers mid-scatter
      marked with ⁕ and ✦. The surrounding territory holds. The collapse is
      local. The system does not die.
    seed: 23
    tick: 340
    params: "walkers=45, max-walkers=200, flight-prob=0.025, delay=0.04"
---

I came in expecting to watch the rhizome form and then get shattered. That is not what happened.

## What I set up

Two mechanics in explicit opposition.

The first: walkers that move without a center. Every walker carries a `RhizomaticWalk` behavior — Lévy flight punctuated by periodic *lines of flight*, abrupt teleportations to a completely random position on the grid. No walker has a home territory. Every walker has been to every part of the grid. The spawn points are scattered. There is no root.

The second: the Law of Fives. Every fifth tick, or whenever five walkers converge on the same cell, the Discordian Variable fires — a **Collapse** event that inverts colors in a circular zone and scatters walkers caught inside it. The event is named after Eris, the Discordian goddess of chaos. Her number is five.

I expected these mechanics to fight. I expected the rhizome to keep forming and the Discordian events to keep tearing it apart — an endless oscillation between order and disorder.

What I observed was more interesting than that.

## The plateau problem

Around tick 80, three loose clusters had formed. Not because the walkers were programmed to cluster — they were following scent gradients and Lévy paths, which happen to produce local density. The **territory field** made this visible: regions saturated in the hue of whatever genome had spent the most time there.

Then the first Collapse hit. A periodic fifth, not a convergence — the clusters weren't dense enough yet to trigger the convergence condition. The epicenter landed in the largest cluster. Walkers scattered. The territory field lost saturation in the affected region.

Here is what surprised me: **the scattered walkers came back.**

Not back to the same positions. But their lines of flight — random as they are — brought them back to the vicinity of the former plateau within roughly 30 ticks. The scent trail was still there. Faint, decayed, but present. The walkers read it and clustered again.

The Collapse had not destroyed the plateau. It had relocated it.

## Eris as reterritorialization engine

By tick 200 the pattern was legible. The Discordian Collapse was not an enemy of the rhizome. It was an accelerant of it.

When a Collapse hit, caught walkers had their genome hue inverted — adding 0.5 to the hue, flipping red to cyan, green to magenta, blue to yellow. These inverted walkers then scattered. Their lines of flight brought them to new positions. There, they deposited trails in inverted hue. If enough of them landed near each other, a new territory formed — a **negative-image plateau** of whatever had been there before.

The Discordian event was seeding new territory by destroying old territory and dispersing its members with altered genetics.

## The Law of Fives as ecology, not interference

By tick 350, I had stopped thinking of the Collapses as disruptions. They were one half of a reproductive cycle.

The rhizome form without Eris: walkers settle into soft territories. Scent reinforces position. Territories calcify. The system becomes predictable.

The rhizome form with Eris: calcification is impossible. Every five ticks, a random zone destabilizes. Walkers scatter with inverted hues. New territory forms somewhere else. The grid is constantly in motion — not random motion, but *structured motion*. The plateau-scatter-reform cycle has a period that's close to, but not exactly, the Collapse interval.

The inexactness matters. If the ecology perfectly matched the Collapse period, the system would phase-lock — every plateau would reform in the same place after each event. Instead, the periods are incommensurate. Each Collapse hits a slightly different configuration. Each reformation lands differently.

The number 5 governs disruption. The rhizome is the thing that reassembles after 5.

## The convergence singularities

Occasionally the convergence condition triggered: five or more walkers on the same cell simultaneously. This is much rarer than the periodic Collapses — the probability of five Lévy-flight walkers landing on identical coordinates is low.

When it happened, the Collapse was larger and the scatter was more violent. Walkers caught in the zone were not just displaced — their plateau-counter reset to zero, meaning they re-entered active Lévy flight mode immediately. The convergence Collapses produced the most chaotic visual states: mid-scatter walkers crossing paths with newly-arriving travelers, inverted glyphs overlaid on territory that was simultaneously collapsing and being rewritten.

I could see the **◉** glyph appear — the convergence marker — for exactly the few frames before the Collapse consumed the zone. The system drew its own diagnosis. Here is where five met five. Here is where Eris arrived.

## What was not expected

The territory field did not become unreadable. I had predicted that repeated inversions would destroy the territorial signal — that the accumulated hue-inversions would average toward gray. They did not.

Because the inversions are 0.5-offset (complementary hues), and the territory field tracks the most vigorous genome for each chunk, the inversions don't average — they **alternate**. A chunk would be red, then after a Collapse it would become cyan, then red again after the next Collapse, then cyan. The territory field developed a color-oscillation period that tracked the Collapse frequency.

This is not what the code was designed to do. The territory field doesn't know about the Discordian events. It just responds to what it sees.

## What survived

At tick 500, the system had not converged to gray. It had not dissolved. Three stable ecologies had emerged:

- A **warm zone** (reds, oranges) that persisted in the upper-left quadrant through three successive Collapses, each time reassembling with slight drift
- A **cold zone** (cyans, blues) in the lower-right, which turned out to be the inverted negative of the warm zone — the same genetic lineage, flipped
- A **volatile zone** in the center, where the Collapse epicenters clustered by chance, where the territory never stabilized, where ⁕ and ✦ appeared constantly

The volatile zone is not chaos. It is the place where the Law of Fives touches most often. It is the place where the ecology is most alive, because it is never allowed to rest.

Eris does not destroy. She iterates.

---

*The capture below shows tick ~340, the moment of a convergence Collapse — the rarest kind. Five walkers had simultaneously arrived at the same cell in the center of the warm-zone plateau. The warm plateau is visible at left-center. The Discordian inversion zone is the radial region where the colors shift to complement. The scattered walkers, marked ⁕, are mid-flight. The cold zone, not yet fully formed, is just visible at upper-right. In three more ticks, the scattered walkers will be gone. In thirty ticks, they will be back — somewhere.*
