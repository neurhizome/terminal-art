#!/usr/bin/env python3
"""
cascade.py — what stops a conversation that has no reason to end?

Composition:
- DiffusionField (src.fields) — attention heat, so a burn is visible as a
  spreading front rather than a number going down
- TerminalStage (src.renderers) — live view
- Genome (src.genetics) — only for stable per-seat hue; no breeding here

THE SYSTEM UNDER STUDY
----------------------
A colony of agents share one relay and one budget. Tagging an agent by name
wakes it, and a woken agent costs the shared pool a turn. Agents reply, and
replies contain names. That is the whole mechanism, and it is enough: two
polite agents naming each other in successive replies will trade turns until
the budget is gone. Nothing in that exchange is a bug. Every message is
individually reasonable.

Two guards were built against this in homelab/buzz on 2026-08-07, and this
experiment exists because their asymmetry was argued rather than measured:

  DEPTH   every auto-reply carries a hop marker; a message that carries one
          summons nobody. Emitted and honoured only by the CC watcher.
  DEFANG  agent names in an auto-reply are neutralised so they match no
          watcher's regex. Applied by the CC watcher to CC replies — but a
          de-fanged name is inert to EVERY lane, including lanes that have
          never heard of this system.

The lanes are not symmetric, and that is the point:

  cc      watcher-backed. Emits markers, honours markers, de-fangs its own
          outgoing replies.
  hermes  gateway-backed, upstream, not ours to change. Emits no marker,
          honours no marker, de-fangs nothing.

So a marker only ever stops a message that carries one, and only CC replies
carry one. Whether that makes DEPTH redundant against DEFANG — or whether it
catches something DEFANG leaks — is exactly what has not been measured.

Ignition is a human: dusty tags somebody. Humans are never de-fanged and
never carry a marker, because a person tagging an agent is the feature.

Run:
  ./cascade.py --regime both               # live
  ./cascade.py --regime none --headless    # data
  ./cascade.py --sweep                     # all regimes x seeds, table
"""

import argparse
import os
import random
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.fields import DiffusionField
from src.renderers.terminal_stage import TerminalStage

REGIMES = ("none", "depth", "defang", "both")

# One summoned turn against the shared window. Units are arbitrary; only the
# ratio to POOL_START matters.
TURN_COST = 1.0


@dataclass
class Seat:
    name: str
    lane: str          # 'cc' | 'hermes'
    x: int
    y: int
    summons: int = 0
    recent: float = 0.0

    @property
    def honours_marker(self) -> bool:
        """Only a lane whose watcher reads the marker can obey it."""
        return self.lane == "cc"

    @property
    def defangs_own_replies(self) -> bool:
        """Only the CC watcher rewrites names on the way out."""
        return self.lane == "cc"


@dataclass
class Message:
    author: str | None      # None = human
    names: list[str]
    depth: int              # 0 for anything a human wrote
    marked: bool            # does it CARRY a depth marker?


@dataclass
class Stats:
    ticks: int = 0
    summons: int = 0
    human_tags: int = 0
    blocked_depth: int = 0
    blocked_defang: int = 0
    blocked_rate: int = 0
    defang_leaks: int = 0
    max_depth: int = 0
    pool_floor: float = 0.0
    extinct_at: int | None = None
    by_lane: dict = field(default_factory=lambda: {"cc": 0, "hermes": 0})


class Colony:
    """The relay, the seats, the shared budget, and the guards."""

    def __init__(self, regime, *, width, height, pool=240.0, rate_cap=0,
                 fanout=(1, 3), human_rate=0.02, regen=0.0,
                 defang_miss=0.0, rng=None):
        if regime not in REGIMES:
            raise ValueError(f"unknown regime {regime!r}")
        self.regime = regime
        self.rng = rng or random.Random()
        self.pool_start = pool
        self.pool = pool
        # Real windows refill — anthropic-sub is a rolling 5h allowance, not a
        # one-shot grant. Without this every regime simply spends the budget
        # and the only question is how fast, which flatters nothing.
        self.regen = regen
        self.defang_miss = defang_miss
        self.rate_cap = rate_cap          # 0 = no cap
        self.fanout = fanout
        self.human_rate = human_rate
        self.stats = Stats(pool_floor=pool)
        self.queue: list[tuple[str, Message]] = []
        self.window: dict[str, list[int]] = {}

        # Roster mirrors the real one: four CC seats, four Hermes seats.
        names = [
            ("opus-5-cc", "cc"), ("haiku-4.5-cc", "cc"),
            ("sonnet-5-cc", "cc"), ("opus-4.8-cc", "cc"),
            ("kimi-k3-ha", "hermes"), ("sol-5.6-ha", "hermes"),
            ("terra-5.6-ha", "hermes"), ("luna-5.6-ha", "hermes"),
        ]
        self.seats = {}
        for i, (name, lane) in enumerate(names):
            angle = (i / len(names)) * 6.28318
            cx, cy = width // 2, height // 2
            radius = min(width, height) * 0.32
            self.seats[name] = Seat(
                name=name, lane=lane,
                x=int(cx + radius * 2.0 * __import__("math").cos(angle)),
                y=int(cy + radius * __import__("math").sin(angle)),
            )

    # -- guards ------------------------------------------------------------

    def _defang_active(self) -> bool:
        return self.regime in ("defang", "both")

    def _depth_active(self) -> bool:
        return self.regime in ("depth", "both")

    def _rate_ok(self, seat: Seat, tick: int) -> bool:
        if not self.rate_cap:
            return True
        recent = [t for t in self.window.get(seat.name, []) if tick - t < 600]
        self.window[seat.name] = recent
        return len(recent) < self.rate_cap

    # -- dynamics ----------------------------------------------------------

    def _compose_reply(self, seat: Seat, incoming_depth: int) -> Message:
        """A woken seat answers, and its answer contains names."""
        k = self.rng.randint(*self.fanout)
        others = [n for n in self.seats if n != seat.name]
        named = self.rng.sample(others, min(k, len(others)))

        # DEFANG: the CC watcher rewrites names on the way out. A de-fanged
        # name is inert to every lane — that is the whole asymmetry.
        #
        # `defang_miss` is not a hedge, it is the whole question. De-fanging
        # works off a roster read from the credential shelf, and a roster can
        # be wrong: on 2026-08-07 an unquoted TOML key silently dropped three
        # of four CC seats from the watcher's own config while the file still
        # read as enabled. A name the roster does not know is a name that
        # goes out live.
        if self._defang_active() and seat.defangs_own_replies:
            survived = [n for n in named if self.rng.random() < self.defang_miss]
            self.stats.blocked_defang += len(named) - len(survived)
            self.stats.defang_leaks += len(survived)
            named = survived

        # DEPTH: the marker is stamped by the same watcher that de-fangs.
        marked = self._depth_active() and seat.defangs_own_replies
        return Message(author=seat.name, names=named,
                       depth=incoming_depth + 1, marked=marked)

    def _deliver(self, message: Message) -> None:
        for name in message.names:
            self.queue.append((name, message))

    def tick(self, tick: int) -> None:
        self.stats.ticks = tick

        # Ignition: a human tags somebody. Never marked, never de-fanged.
        if self.rng.random() < self.human_rate:
            target = self.rng.choice(list(self.seats))
            self.stats.human_tags += 1
            self._deliver(Message(author=None, names=[target], depth=0,
                                  marked=False))

        pending, self.queue = self.queue, []
        for name, message in pending:
            seat = self.seats[name]

            # DEPTH only ever stops a message that CARRIES a marker, and only
            # for a seat whose watcher reads them.
            if self._depth_active() and message.marked and seat.honours_marker:
                self.stats.blocked_depth += 1
                continue
            if not self._rate_ok(seat, tick):
                self.stats.blocked_rate += 1
                continue
            if self.pool <= 0:
                continue

            self.pool -= TURN_COST
            seat.summons += 1
            seat.recent = 1.0
            self.stats.summons += 1
            self.stats.by_lane[seat.lane] += 1
            self.stats.max_depth = max(self.stats.max_depth, message.depth)
            self.window.setdefault(name, []).append(tick)
            self._deliver(self._compose_reply(seat, message.depth))

        self.pool = min(self.pool_start, self.pool + self.regen)
        self.pool_floor = self.stats.pool_floor = min(self.stats.pool_floor,
                                                      self.pool)
        if self.pool <= 0 and self.stats.extinct_at is None:
            self.stats.extinct_at = tick

        for seat in self.seats.values():
            seat.recent *= 0.90


def run_headless(regime, ticks, seed, **kw):
    colony = Colony(regime, width=120, height=32, rng=random.Random(seed), **kw)
    for t in range(ticks):
        colony.tick(t)
    return colony


GLYPHS = " ·:+*#%@"


def run_live(regime, ticks, seed, delay, **kw):
    with TerminalStage() as stage:
        width, height = stage.width, stage.height
        colony = Colony(regime, width=width, height=height,
                        rng=random.Random(seed), **kw)
        heat = DiffusionField(width, height, diffusion_rate=0.18,
                              decay_rate=0.93)
        for t in range(ticks):
            colony.tick(t)
            for seat in colony.seats.values():
                if seat.recent > 0.05:
                    heat.deposit(seat.x, seat.y, seat.recent * 2.0)
            heat.update()
            stage.clear()

            for y in range(height):
                for x in range(width):
                    v = heat.get(x, y)
                    if v > 0.02:
                        idx = min(len(GLYPHS) - 1, int(v * 6))
                        stage.set_cell(x, y, GLYPHS[idx])

            for seat in colony.seats.values():
                mark = "◈" if seat.lane == "cc" else "◇"
                for i, ch in enumerate(f"{mark} {seat.name}"):
                    if 0 <= seat.x + i < width:
                        stage.set_cell(seat.x + i, seat.y, ch)

            filled = int(30 * max(0.0, colony.pool) / colony.pool_start)
            bar = "█" * filled + "░" * (30 - filled)
            head = (f"THE CASCADE · regime={regime} · t={t} · pool[{bar}] "
                    f"{max(0.0, colony.pool):6.1f} · summons={colony.stats.summons}")
            for i, ch in enumerate(head[:width]):
                stage.set_cell(i, 0, ch)
            stage.render()
            time.sleep(delay)
            if colony.stats.extinct_at is not None:
                time.sleep(1.2)
                break
        return colony


def record_frames(regime, ticks, seed, out_dir, *, width=104, height=30,
                 every=2, **kw):
    """Write one .ans per sampled tick so ansi_render.py can encode a video.

    Headless on purpose: the live view needs a TTY, and a burn that only
    exists while someone is watching it cannot be published.
    """
    import math
    out_dir.mkdir(parents=True, exist_ok=True)
    colony = Colony(regime, width=width, height=height,
                    rng=random.Random(seed), **kw)
    heat = DiffusionField(width, height, diffusion_rate=0.18, decay_rate=0.90)
    n = 0
    for t in range(ticks):
        colony.tick(t)
        for seat in colony.seats.values():
            if seat.recent > 0.05:
                heat.deposit(seat.x, seat.y, seat.recent * 2.5)
        heat.update()
        if t % every:
            continue
        # Heat ramps cool->hot so a spreading burn reads as temperature
        # rather than as density. Colour is the whole reason the video is
        # more legible than the numbers.
        ramp = ["\033[38;5;24m", "\033[38;5;31m", "\033[38;5;38m",
                "\033[38;5;73m", "\033[38;5;179m", "\033[38;5;208m",
                "\033[38;5;203m", "\033[38;5;197m"]
        grid = [[" "] * width for _ in range(height)]
        for y in range(height):
            for x in range(width):
                v = heat.get(x, y)
                if v > 0.02:
                    i = min(len(GLYPHS) - 1, int(v * 6))
                    grid[y][x] = f"{ramp[min(len(ramp) - 1, i)]}{GLYPHS[i]}\033[0m"
        for seat in colony.seats.values():
            mark = "\u25c8" if seat.lane == "cc" else "\u25c7"
            # Bright while burning, dim while idle — a woken seat should be
            # visibly the thing that just cost something.
            hot = seat.recent > 0.25
            col = ("\033[38;5;231m" if hot else
                   ("\033[38;5;117m" if seat.lane == "cc" else "\033[38;5;215m"))
            label = f"{mark} {seat.name}"
            for i, chx in enumerate(label):
                if 0 <= seat.x + i < width and 0 <= seat.y < height:
                    grid[seat.y][seat.x + i] = f"{col}{chx}\033[0m"
        filled = int(30 * max(0.0, colony.pool) / colony.pool_start)
        bar = "\u2588" * filled + "\u2591" * (30 - filled)
        frac = max(0.0, colony.pool) / colony.pool_start
        pool_col = ("\033[38;5;79m" if frac > 0.5 else
                    "\033[38;5;215m" if frac > 0.15 else "\033[38;5;203m")
        head = (f"\033[38;5;255mTHE CASCADE\033[0m  \033[38;5;250mregime="
                f"{regime:<7}\033[0m \033[38;5;240mt={t:<5}\033[0m "
                f"{pool_col}[{bar}] {max(0.0, colony.pool):6.1f}\033[0m  "
                f"\033[38;5;240msummons={colony.stats.summons}\033[0m")
        body = "\n".join("".join(r) for r in grid)
        (out_dir / f"f{n:05d}.ans").write_text(head + "\n" + body + "\n",
                                               encoding="utf-8")
        n += 1
    return n


def sweep(ticks, seeds, **kw):
    print(f"\nTHE CASCADE — {len(seeds)} seeds x {ticks} ticks, "
          f"pool={kw.get('pool', 240.0):.0f}, cost={TURN_COST}/turn\n")
    header = (f"{'regime':8} {'survived':>9} {'died at':>9} {'summons':>9} "
              f"{'floor':>7} {'max hop':>8} {'cc':>6} {'hermes':>7}")
    print(header)
    print("-" * len(header))
    results = {}
    for regime in REGIMES:
        runs = [run_headless(regime, ticks, seed, **kw) for seed in seeds]
        alive = sum(1 for c in runs if c.stats.extinct_at is None)
        died = [c.stats.extinct_at for c in runs if c.stats.extinct_at is not None]
        when = f"{sum(died)/len(died):.0f}" if died else "—"
        summons = sum(c.stats.summons for c in runs) / len(runs)
        floor = sum(c.stats.pool_floor for c in runs) / len(runs)
        hop = max(c.stats.max_depth for c in runs)
        cc = sum(c.stats.by_lane["cc"] for c in runs) / len(runs)
        he = sum(c.stats.by_lane["hermes"] for c in runs) / len(runs)
        results[regime] = runs
        print(f"{regime:8} {alive:>4}/{len(seeds):<4} {when:>9} {summons:>9.0f} "
              f"{floor:>7.1f} {hop:>8} {cc:>6.0f} {he:>7.0f}")
    print()
    return results


def main():
    p = argparse.ArgumentParser(description="The Cascade")
    p.add_argument("--regime", choices=REGIMES, default="both")
    p.add_argument("--ticks", type=int, default=2000)
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--seeds", type=int, default=12, help="sweep seed count")
    p.add_argument("--pool", type=float, default=240.0)
    p.add_argument("--rate-cap", type=int, default=0,
                   help="max summons per seat per 600 ticks (0 = none)")
    p.add_argument("--human-rate", type=float, default=0.02)
    p.add_argument("--defang-miss", type=float, default=0.0,
                   help="fraction of names a stale roster fails to de-fang")
    p.add_argument("--regen", type=float, default=0.25,
                   help="pool refill per tick (rolling window)")
    p.add_argument("--delay", type=float, default=0.04)
    p.add_argument("--headless", action="store_true")
    p.add_argument("--sweep", action="store_true")
    p.add_argument("--record", type=Path,
                   help="write .ans frames to this directory")
    a = p.parse_args()

    kw = dict(pool=a.pool, rate_cap=a.rate_cap, human_rate=a.human_rate,
              regen=a.regen, defang_miss=a.defang_miss)

    if a.record:
        n = record_frames(a.regime, a.ticks, a.seed, a.record, **kw)
        print(f"wrote {n} frames to {a.record}")
        return

    if a.sweep:
        sweep(a.ticks, list(range(a.seeds)), **kw)
        return

    if a.headless:
        c = run_headless(a.regime, a.ticks, a.seed, **kw)
    else:
        c = run_live(a.regime, a.ticks, a.seed, a.delay, **kw)

    s = c.stats
    print(f"\nregime={a.regime} seed={a.seed}")
    print(f"  summons        {s.summons}  (cc {s.by_lane['cc']} / "
          f"hermes {s.by_lane['hermes']})")
    print(f"  human tags     {s.human_tags}")
    print(f"  max hop depth  {s.max_depth}")
    print(f"  blocked        depth={s.blocked_depth} "
          f"defang={s.blocked_defang} rate={s.blocked_rate} "
          f"(leaked {s.defang_leaks})")
    print(f"  pool           {max(0.0, c.pool):.1f} / {c.pool_start:.0f}")
    print(f"  extinct at     {s.extinct_at}\n")


if __name__ == "__main__":
    main()
