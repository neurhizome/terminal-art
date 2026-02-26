#!/usr/bin/env python3
"""
rhizomatic_walker.py — Rhizome dynamics + Discordian interference

Two forces in tension:

1. Rhizomatic walkers: form plateaus, break off, restart anywhere.
   No center. No root. Lines of flight across the whole terminal plane.

2. The Law of Fives: every 5th cycle multiple, or when 5 walkers
   converge on the same cell, the Discordian Variable triggers —
   a localized color inversion and walker scatter called the Collapse.

Conceptual basis:
- Deleuze & Guattari's rhizome: horizontal, acentric, multiplicitous.
  A rhizome has no beginning and no end. It is always in the middle.
- Discordian Law of Fives: all things happen in 5s (or multiples thereof).
  The number 5 governs chaotic disruption. Hail Eris.

The tension: rhizomatic spread wants to form stable patches (plateaus).
The Discordian Collapse shatters them locally. The system oscillates
between self-organization and principled disorder.

Usage:
    python3 experiments/rhizomatic_walker.py
    python3 experiments/rhizomatic_walker.py --walkers 60 --seed 23
    python3 experiments/rhizomatic_walker.py --walkers 80 --delay 0.02 --flight-prob 0.02
"""

import sys
import os
import time
import random
import math
import argparse
import colorsys
import collections
from typing import Tuple, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.automata import Walker, Spawner
from src.automata.behaviors import MovementBehavior, LevyFlight
from src.genetics import Genome
from src.fields import DiffusionField, TerritoryField
from src.renderers.terminal_stage import TerminalStage


# --- Rhizomatic Movement ---

class RhizomaticWalk(MovementBehavior):
    """
    Acentric movement in the Deleuzian sense.

    Operates in two modes:
    - Active: Lévy flight — short local steps punctuated by rare long jumps
    - Plateau: micro-jitter while clustering with neighbors

    Periodically fires a 'line of flight' — an abrupt deterritorialization
    that relocates the walker anywhere on the grid. Not escape. Becoming-other.
    The plateau counter resets on each line of flight.
    """

    def __init__(self, width: int, height: int,
                 flight_prob: float = 0.025,
                 plateau_threshold: int = 45):
        self.width = width
        self.height = height
        self.flight_prob = flight_prob
        self.plateau_threshold = plateau_threshold
        self._levy = LevyFlight(alpha=1.5, scale=1.1)
        self._plateau_counter = 0
        self._ticks_to_flight = self._draw_flight_interval()

    def _draw_flight_interval(self) -> int:
        """Exponentially distributed time between lines of flight."""
        return max(30, int(random.expovariate(1.0 / 90)))

    def get_move(self, x: int, y: int, **context) -> Tuple[int, int]:
        self._plateau_counter += 1
        self._ticks_to_flight -= 1

        # Line of flight: abrupt deterritorialization to a new territory
        if self._ticks_to_flight <= 0:
            self._ticks_to_flight = self._draw_flight_interval()
            self._plateau_counter = 0
            nx = random.randint(0, self.width - 1)
            ny = random.randint(0, self.height - 1)
            return (nx - x, ny - y)

        # Plateau mode: micro-drift when settled
        if self._plateau_counter > self.plateau_threshold:
            return random.choice([
                (0, -1), (1, 0), (0, 1), (-1, 0),
                (0, 0), (0, 0)          # bias toward stillness in plateau
            ])

        # Active rhizomatic traversal via Lévy flight
        return self._levy.get_move(x, y)


# --- Discordian Color Logic ---

def discordian_invert(r: int, g: int, b: int) -> Tuple[int, int, int]:
    """
    Law of Fives color inversion: rotate hue 180°, force brightness.

    Complementary hue + boosted saturation + near-maximum value.
    The visual signature of Eris arriving.
    """
    h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    h = (h + 0.5) % 1.0
    s = min(1.0, s + 0.35)
    v = max(0.85, v)
    nr, ng, nb = colorsys.hsv_to_rgb(h, s, v)
    return (int(nr * 255), int(ng * 255), int(nb * 255))


# --- Main Experiment ---

def main():
    parser = argparse.ArgumentParser(description="Rhizomatic Walker — Discordian Chaos Engine")
    parser.add_argument('--walkers', type=int, default=45,
                        help='Initial walker population (default: 45)')
    parser.add_argument('--max-walkers', type=int, default=200,
                        help='Maximum population cap (default: 200)')
    parser.add_argument('--delay', type=float, default=0.04,
                        help='Frame delay in seconds (default: 0.04)')
    parser.add_argument('--flight-prob', type=float, default=0.025,
                        help='Probability of line-of-flight per step (default: 0.025)')
    parser.add_argument('--seed', type=int, default=None,
                        help='Random seed for reproducibility')
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    with TerminalStage() as stage:
        width, height = stage.width, stage.height

        # Core components
        spawner = Spawner(max_walkers=args.max_walkers, width=width, height=height)
        scent = DiffusionField(width, height, diffusion_rate=0.15, decay_rate=0.92)
        territory = TerritoryField(width, height, chunk_size=6)

        # Behavior registry: walker id → behavior instance
        behaviors: dict = {}

        def spawn_rhizomatic(genome: Optional[Genome] = None,
                              x: Optional[int] = None,
                              y: Optional[int] = None) -> Optional[Walker]:
            """Spawn a walker and register its rhizomatic behavior."""
            g = genome or Genome(color_h=random.random(),
                                 vigor=random.uniform(0.8, 1.2))
            if x is not None and y is not None:
                w = spawner.spawn_at(x, y, genome=g, char='·')
            else:
                w = spawner.spawn_random(genome=g, char='·')
            if w:
                behaviors[id(w)] = RhizomaticWalk(
                    width, height,
                    flight_prob=args.flight_prob
                )
            return w

        # Initial population: scattered rhizomatically (no single origin)
        for _ in range(args.walkers):
            spawn_rhizomatic()

        # Discordian state
        discordian_active = False
        discordian_ticks_remaining = 0
        discordian_cells: set = set()
        total_collapses = 0

        # Law of Fives counter
        fifth_counter = 0

        # Cell occupancy tracking (per-tick)
        cell_occupancy: collections.Counter = collections.Counter()

        tick = 0

        try:
            while True:
                # === UPDATE PHASE ===

                spawner.age_all()
                cell_occupancy.clear()

                # Tally walker positions for occupancy
                for w in spawner.walkers:
                    cell_occupancy[(w.x, w.y)] += 1

                # --- Discordian Trigger Logic ---
                # Trigger condition A: 5+ walkers sharing one cell
                convergence_points = [
                    pos for pos, count in cell_occupancy.items() if count >= 5
                ]

                # Trigger condition B: tick is a multiple of 5 (fifth_counter wraps)
                fifth_counter = (fifth_counter + 1) % 5
                periodic_fifth = (fifth_counter == 0)

                should_trigger = (len(convergence_points) > 0 or periodic_fifth)

                if should_trigger and not discordian_active:
                    discordian_active = True
                    discordian_ticks_remaining = random.randint(10, 22)
                    total_collapses += 1

                    # Collapse epicenter
                    if convergence_points:
                        cx, cy = random.choice(convergence_points)
                    else:
                        # Periodic fifth: random position, slightly biased toward center
                        cx = int(random.gauss(width / 2, width / 5)) % width
                        cy = int(random.gauss(height / 2, height / 5)) % height

                    # Collapse zone: circular region
                    collapse_radius = random.randint(7, 18)
                    discordian_cells = set()
                    r2 = collapse_radius * collapse_radius
                    for dy in range(-collapse_radius, collapse_radius + 1):
                        for dx in range(-collapse_radius, collapse_radius + 1):
                            if dx * dx + dy * dy <= r2:
                                nx = (cx + dx) % width
                                ny = (cy + dy) % height
                                discordian_cells.add((nx, ny))

                    # Affect walkers in collapse zone
                    for w in spawner.walkers:
                        if (w.x, w.y) in discordian_cells:
                            # Hue inversion (genetic marker of the event)
                            w.genome.color_h = (w.genome.color_h + 0.5) % 1.0
                            w.vigor = max(0.2, w.vigor)
                            # 60% chance: line of flight out of collapse zone
                            if random.random() < 0.6:
                                w.x = random.randint(0, width - 1)
                                w.y = random.randint(0, height - 1)
                                beh = behaviors.get(id(w))
                                if beh:
                                    beh._plateau_counter = 0  # break out of plateau

                if discordian_active:
                    discordian_ticks_remaining -= 1
                    if discordian_ticks_remaining <= 0:
                        discordian_active = False
                        discordian_cells = set()

                # --- Walker Movement ---
                for w in spawner.walkers:
                    behavior = behaviors.get(id(w))
                    if behavior is None:
                        behavior = RhizomaticWalk(width, height, flight_prob=args.flight_prob)
                        behaviors[id(w)] = behavior

                    scent.deposit(w.x, w.y, w.vigor * 0.4)
                    territory.claim(w)

                    dx, dy = behavior.get_move(w.x, w.y, field=scent)
                    w.move(dx, dy, width, height, wrap=True)

                # --- Reproduction at plateaus ---
                if not spawner.is_full() and random.random() < 0.04:
                    if spawner.walkers:
                        parent = random.choice(spawner.walkers)
                        partners = spawner.find_breeding_partners(parent, radius=6.0,
                                                                   threshold=0.3)
                        if partners:
                            partner = random.choice(partners)
                            child = spawner.spawn_from_parents(
                                parent, partner, mutation_rate=0.05
                            )
                            if child:
                                behaviors[id(child)] = RhizomaticWalk(
                                    width, height, flight_prob=args.flight_prob
                                )

                # --- Death and cleanup ---
                alive_ids_before = {id(w) for w in spawner.walkers}
                spawner.remove_dead(max_age=700, vigor_threshold=0.1)
                alive_ids_after = {id(w) for w in spawner.walkers}
                for wid in (alive_ids_before - alive_ids_after):
                    behaviors.pop(wid, None)

                # Maintain minimum viable population
                floor = max(10, args.walkers // 4)
                while len(spawner.walkers) < floor:
                    spawn_rhizomatic()

                # --- Field dynamics ---
                scent.update()
                territory.update()
                active_ids = {id(w) for w in spawner.walkers}
                territory.prune_genomes(active_ids)

                # === RENDER PHASE ===

                stage.clear()

                # Background: territory colors
                t_render = territory.render()
                for y in range(height):
                    for x in range(width):
                        char, fg, bg = t_render[y][x]
                        stage.cells[y][x].char = char
                        stage.cells[y][x].fg_color = fg
                        stage.cells[y][x].bg_color = bg

                # Discordian zone: invert colors in collapse radius
                if discordian_active:
                    for (cx, cy) in discordian_cells:
                        if 0 <= cy < height and 0 <= cx < width:
                            cell = stage.cells[cy][cx]
                            fg = cell.fg_color or (180, 180, 180)
                            bg = cell.bg_color or (0, 0, 0)
                            cell.fg_color = discordian_invert(*fg)
                            cell.bg_color = discordian_invert(*bg)
                            if random.random() < 0.25:
                                cell.char = random.choice(['⁕', '✦', '⊛', '◈', '⋆'])

                # Foreground: walkers
                for w in spawner.walkers:
                    if 0 <= w.x < width and 0 <= w.y < height:
                        r, g, b = w.genome.to_rgb()
                        in_collapse = discordian_active and (w.x, w.y) in discordian_cells
                        occ = cell_occupancy.get((w.x, w.y), 1)

                        if in_collapse:
                            r, g, b = discordian_invert(r, g, b)
                            char = random.choice(['⁕', '✦', '⊛'])
                        elif occ >= 5:
                            char = '◉'   # convergence point (Law of Fives marker)
                        elif occ >= 3:
                            char = '●'   # dense cluster
                        else:
                            char = '·'

                        stage.cells[w.y][w.x].char = char
                        stage.cells[w.y][w.x].fg_color = (r, g, b)

                # Status line
                stats = spawner.get_stats()
                plateau_count = sum(1 for c in cell_occupancy.values() if c >= 3)
                convergence_count = sum(1 for c in cell_occupancy.values() if c >= 5)

                collapse_indicator = '⁕ ERIS ARRIVES ⁕' if discordian_active else ' ' * 17
                status = (
                    f"Tick:{tick:5d} | "
                    f"Pop:{stats['count']:3d}/{args.max_walkers} | "
                    f"Plateaus:{plateau_count:3d} | "
                    f"Convergences:{convergence_count:2d} | "
                    f"Collapses:{total_collapses:4d} | "
                    f"{collapse_indicator}"
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
