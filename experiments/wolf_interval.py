#!/usr/bin/env python3
"""
wolf_interval.py - The Pythagorean comma made visible

Walkers carry pitch genomes (color_h = octave position on the HSV wheel).
They seek neighbours at the Pythagorean fifth distance (log2(1.5) ≈ 0.58496)
and tune toward them each tick.

Every local tuning decision is correct. Globally, the comma accumulates:
12 pure fifths overshoot 7 octaves by 23.46 cents. The hue distribution
drifts irresistibly around the colour wheel. A wolf shadow — the gap where
no walker wants to be — emerges spontaneously around tick 1000.

At tick 500 an EqualTemperament event snaps every hue to the nearest
semitone. The drift restarts from silence, faster the second time.
"""

import sys
import os
import time
import math
import random
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.automata import Walker, Spawner, FifthSeek, RandomWalk
from src.genetics import Genome
from src.genetics.genome import circular_mean, circular_distance
from src.fields import DiffusionField
from src.events import EventScheduler, EqualTemperament
from src.renderers.terminal_stage import TerminalStage

# ── tuning constants ──────────────────────────────────────────────────────────

PYTHAGOREAN_FIFTH = math.log2(1.5)   # ≈ 0.58496…  (the pure fifth)
EQUAL_FIFTH       = 7 / 12           # ≈ 0.58333…  (equal temperament)
COMMA             = PYTHAGOREAN_FIFTH - EQUAL_FIFTH  # ≈ 0.00163 per fifth

FIFTH_TOLERANCE  = 0.035   # hue band that counts as "at a fifth"
SPATIAL_RADIUS   = 10.0    # cells to search for a fifth partner
WOLF_BIN_THRESH  = 0.35    # bin fraction below this → wolf gap detected


# ── helpers ───────────────────────────────────────────────────────────────────

def find_fifth_partner(walker, walkers, radius=SPATIAL_RADIUS):
    """Return nearest walker whose hue is ~one Pythagorean fifth above ours."""
    target_h = (walker.genome.color_h + PYTHAGOREAN_FIFTH) % 1.0
    best, best_sdist = None, float('inf')
    for other in walkers:
        if other is walker:
            continue
        sdist = walker.distance_to(other)
        if sdist > radius:
            continue
        hdist = circular_distance(other.genome.color_h, target_h)
        if hdist < FIFTH_TOLERANCE and sdist < best_sdist:
            best, best_sdist = other, sdist
    return best


def mean_hue(walkers):
    if not walkers:
        return 0.0
    return circular_mean([w.genome.color_h for w in walkers])


def wolf_status(walkers, n_bins=12):
    """Return (gap_detected, gap_bin, gap_fraction) from hue histogram."""
    bins = [0] * n_bins
    for w in walkers:
        bins[int(w.genome.color_h * n_bins) % n_bins] += 1
    if not walkers:
        return False, -1, 0.0
    expected = len(walkers) / n_bins
    min_bin  = min(range(n_bins), key=lambda i: bins[i])
    frac     = bins[min_bin] / expected if expected > 0 else 1.0
    return frac < WOLF_BIN_THRESH, min_bin, frac


def walker_color(walker, resonating):
    """HSV → RGB for a walker, boosted if currently resonating."""
    import colorsys
    h = walker.genome.color_h
    s = 0.95 if walker in resonating else 0.65
    v = 0.95 if walker in resonating else 0.75
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return int(r * 255), int(g * 255), int(b * 255)


def walker_char(walker, wolf_bin, resonating):
    """Choose display glyph based on tuning state."""
    h_bin = int(walker.genome.color_h * 12) % 12
    if h_bin == wolf_bin:
        return '▓'       # stranded at the wolf
    if walker in resonating:
        return '◉'       # actively resonating with a fifth partner
    return '●'


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Wolf Interval — Pythagorean comma drift experiment"
    )
    parser.add_argument('--walkers', type=int, default=200,
                        help='Population size (default 200)')
    parser.add_argument('--tune-rate', type=float, default=0.0008,
                        help='Hue tuning step per fifth encounter (default 0.0008)')
    parser.add_argument('--delay', type=float, default=0.04,
                        help='Seconds between frames (default 0.04)')
    parser.add_argument('--et-tick', type=int, default=500,
                        help='Tick at which EqualTemperament fires (default 500)')
    parser.add_argument('--seed', type=int, default=None,
                        help='Random seed for reproducibility')
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    fifth_seek  = FifthSeek()
    random_walk = RandomWalk(eight_way=True)

    with TerminalStage() as stage:
        width, height = stage.width, stage.height

        # ── initialise population ──────────────────────────────────────────
        spawner = Spawner(max_walkers=args.walkers, width=width, height=height)

        # Spread walkers uniformly across the full hue wheel
        for i in range(args.walkers):
            h = i / args.walkers          # even spacing [0, 1)
            h += random.gauss(0, 0.02)    # small jitter
            genome = Genome(
                color_h=h % 1.0,
                vigor=random.uniform(0.8, 1.2),
                saturation=0.85,
                value=0.9,
            )
            spawner.spawn_random(genome=genome, char='●')

        # ── resonance scent field ──────────────────────────────────────────
        # Deposited wherever a fifth-pair meeting occurs.
        # Traces the circle-of-fifths topology on the grid floor.
        resonance = DiffusionField(
            width, height,
            diffusion_rate=0.15,
            decay_rate=0.93,
        )

        # ── event scheduler ────────────────────────────────────────────────
        scheduler = EventScheduler()
        et_fired  = False

        system = {'spawner': spawner, 'field': resonance, 'config': {}}

        # Track hue at session start to measure cumulative drift
        start_hue = mean_hue(spawner.walkers)
        tick = 0

        try:
            while True:

                # ── fire EqualTemperament once ─────────────────────────────
                if not et_fired and tick == args.et_tick:
                    scheduler.add(EqualTemperament(duration=80))
                    et_fired = True

                # ── update events ──────────────────────────────────────────
                scheduler.update(system)

                # ── walker update ──────────────────────────────────────────
                resonating = set()

                for walker in spawner.walkers:
                    partner = find_fifth_partner(walker, spawner.walkers)

                    if partner is not None:
                        # Tune: shift color_h toward the Pythagorean fifth
                        walker.genome.tune_toward(partner.genome, rate=args.tune_rate)

                        # Deposit resonance scent at the meeting point
                        mid_x = (walker.x + partner.x) // 2
                        mid_y = (walker.y + partner.y) // 2
                        resonance.deposit(mid_x % width, mid_y % height, 1.5)

                        resonating.add(walker)

                        # Move toward the partner
                        dx, dy = fifth_seek.get_move(
                            walker.x, walker.y,
                            target_x=partner.x, target_y=partner.y,
                        )
                    else:
                        # No fifth partner nearby — wander
                        dx, dy = random_walk.get_move(walker.x, walker.y)

                    walker.move(dx, dy, width, height, wrap=True)

                spawner.age_all()

                # Respawn walkers that wander off — keep population stable.
                # Dead walkers replaced with a child of two random survivors.
                spawner.remove_dead(max_age=800, vigor_threshold=0.05)
                while not spawner.is_full() and len(spawner.walkers) >= 2:
                    p1, p2 = random.sample(spawner.walkers, 2)
                    spawner.spawn_from_parents(p1, p2, mutation_rate=0.02)

                resonance.update()

                # ── render ─────────────────────────────────────────────────
                stage.clear()

                # Background: resonance scent field
                res_render = resonance.render()
                for y in range(height):
                    for x in range(width):
                        char, fg, bg = res_render[y][x]
                        stage.cells[y][x].char     = char
                        stage.cells[y][x].fg_color = fg
                        stage.cells[y][x].bg_color = bg

                # Foreground: walkers
                wolf_gap, wolf_bin, wolf_frac = wolf_status(spawner.walkers)
                for walker in spawner.walkers:
                    wx, wy = walker.x, walker.y
                    if 0 <= wx < width and 0 <= wy < height:
                        r, g, b = walker_color(walker, resonating)
                        stage.cells[wy][wx].char     = walker_char(walker, wolf_bin, resonating)
                        stage.cells[wy][wx].fg_color = (r, g, b)

                # ── status line ────────────────────────────────────────────
                cur_hue   = mean_hue(spawner.walkers)
                drift     = (cur_hue - start_hue) % 1.0
                if drift > 0.5:
                    drift -= 1.0
                drift_cents = drift * 1200   # convert to cents (1200c = 1 octave)

                wolf_str = (
                    f"WOLF bin={wolf_bin:2d} [{wolf_frac:.0%}]"
                    if wolf_gap else "no wolf   "
                )

                ev_str = scheduler.get_status_line() if scheduler.events else "         "

                status = (
                    f"tick {tick:6d} | "
                    f"pop {len(spawner.walkers):3d} | "
                    f"mean-h {cur_hue:.4f} | "
                    f"drift {drift_cents:+.1f}¢ | "
                    f"{wolf_str} | "
                    f"{ev_str}"
                )

                stage.render_diff()
                sys.stdout.write(f"\x1b[{height + 1};1H{status}\x1b[K")
                sys.stdout.flush()

                time.sleep(args.delay)
                tick += 1

        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
