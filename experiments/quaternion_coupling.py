#!/usr/bin/env python3
"""
quaternion_coupling.py — Non-commutative colour genetics and the seam as comma

Two populations seeded on opposite halves of the grid with different hues.
Each genome is a unit quaternion (qw, qi, qj, qk):

    hue         ← i-j equatorial angle
    brightness  ← qw scalar
    affinity    ← |qk|  (coupling strength — invisible in colour, governs
                          how powerfully reproduction seeks coherence)

Reproduction is via Hamilton product: parent_A.reproduce_with(parent_B)
gives a different child from parent_B.reproduce_with(parent_A).  The seam
between the two populations is not symmetric — crossings from the left land
in different colour territory than crossings from the right.

This is the spatial comma: the boundary is the incommensurability made
visible, equivalent to the wolf interval in the Pythagorean tuning session.

Watch for:
  ∘  Asymmetric seam colours (the territory each side creates in the middle)
  ∘  Resonance bands — bright, high-affinity walkers accumulating where both
     populations have met and coupled repeatedly (the BLUECOW009 coherence zone)
  ∘  'Dominant crossing' — when a high-vigor walker crosses, its coupling
     pulls offspring much further from the home-side hue than a weak walker

Tune --affinity to find the coherence window:
    0.05  →  nearly commutative; seam looks symmetric, like Sessions 001-003
    0.35  →  the sweet spot; resonance bands appear along the seam
    0.80  →  overcoupled; offspring collapse toward a single hue
"""

import sys
import os
import math
import time
import random
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.automata import Walker, Spawner, RandomWalk, GradientFollow
from src.genetics import QuaternionGenome
from src.fields import DiffusionField, TerritoryField
from src.renderers.terminal_stage import TerminalStage


# ── helpers ───────────────────────────────────────────────────────────────────

def make_population(n, hue, affinity, vigor_range=(0.8, 1.2)):
    """Generate a list of QuaternionGenomes centred on a hue."""
    pop = []
    for _ in range(n):
        h = (hue + random.gauss(0, 0.03)) % 1.0
        aff = max(0.0, min(0.99, affinity + random.gauss(0, 0.05)))
        v = random.uniform(*vigor_range)
        pop.append(QuaternionGenome.from_hue(h, affinity=aff, vigor=v))
    return pop


def affinity_char(genome):
    """Glyph that shows coupling strength (affinity) of the walker."""
    a = genome.resonance_affinity
    if a < 0.15:
        return '·'    # weakly coupled
    if a < 0.35:
        return '○'    # moderate
    if a < 0.55:
        return '●'    # standard
    if a < 0.75:
        return '◉'    # high affinity
    return '⬟'        # overcoupled — watch these


def affinity_boost(genome):
    """Brightness multiplier for rendering; high-affinity walkers glow."""
    a = genome.resonance_affinity
    return 0.6 + 0.4 * a


def seam_stats(spawner, width):
    """Return fraction of each half occupied by the 'other' colour."""
    left_in_right = 0
    right_in_left = 0
    mid = width // 2
    for w in spawner.walkers:
        h = w.genome.color_h
        is_warm = h < 0.25 or h > 0.85   # reds/purples = right-side lineage
        if w.x < mid and is_warm:
            right_in_left += 1
        elif w.x >= mid and not is_warm:
            left_in_right += 1
    n = len(spawner.walkers) or 1
    return left_in_right / n, right_in_left / n


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Quaternion Coupling — non-commutative colour genetics"
    )
    parser.add_argument('--walkers', type=int, default=180,
                        help='Total walkers, split equally between populations')
    parser.add_argument('--affinity', type=float, default=0.35,
                        help='Initial resonance affinity |qk| (default 0.35). '
                             'Try 0.05 (near-commutative) to 0.80 (overcoupled).')
    parser.add_argument('--delay', type=float, default=0.04,
                        help='Seconds between frames')
    parser.add_argument('--breed-radius', type=float, default=6.0,
                        help='Spatial radius for finding breeding partners')
    parser.add_argument('--seed', type=int, default=None)
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    random_walk  = RandomWalk(eight_way=True)

    with TerminalStage() as stage:
        width, height = stage.width, stage.height
        mid = width // 2

        # ── initialise two populations ─────────────────────────────────────
        spawner = Spawner(max_walkers=args.walkers, width=width, height=height)

        # Left lineage: green-cyan  (hue ≈ 0.33)
        left_genomes  = make_population(args.walkers // 2, hue=0.33,
                                        affinity=args.affinity)
        # Right lineage: red-orange  (hue ≈ 0.0)
        right_genomes = make_population(args.walkers // 2, hue=0.0,
                                        affinity=args.affinity)

        for genome in left_genomes:
            x = random.randint(0, mid - 1)
            y = random.randint(0, height - 1)
            spawner.spawn_at(x, y, genome=genome)

        for genome in right_genomes:
            x = random.randint(mid, width - 1)
            y = random.randint(0, height - 1)
            spawner.spawn_at(x, y, genome=genome)

        # ── fields ────────────────────────────────────────────────────────
        # Scent field: walkers deposit trail, gradient-follow their own side
        scent = DiffusionField(width, height, diffusion_rate=0.18, decay_rate=0.94)
        # Territory: tracks which lineage owns each chunk
        territory = TerritoryField(width, height, chunk_size=6)

        tick = 0

        try:
            while True:

                # ── walker update ──────────────────────────────────────────
                spawner.age_all()

                for walker in spawner.walkers:
                    genome = walker.genome   # QuaternionGenome

                    # Deposit scent proportional to vigor
                    scent.deposit(walker.x, walker.y, genome.vigor * 0.5)
                    territory.claim(walker)

                    # Movement: follow scent or wander
                    if random.random() < 0.65:
                        dx, dy = GradientFollow('scent', attraction=True).get_move(
                            walker.x, walker.y, field=scent
                        )
                    else:
                        dx, dy = random_walk.get_move(walker.x, walker.y)

                    walker.move(dx, dy, width, height, wrap=True)

                # ── reproduction ───────────────────────────────────────────
                # Non-commutative: the walker that "initiates" is dominant.
                if not spawner.is_full() and random.random() < 0.06:
                    initiator = random.choice(spawner.walkers)
                    partners = spawner.find_neighbors(initiator, args.breed_radius)
                    compatible = [
                        p for p in partners
                        if initiator.genome.can_breed_with(p.genome)
                    ]
                    if compatible:
                        partner = random.choice(compatible)

                        # Initiator is dominant parent
                        child_genome = initiator.genome.reproduce_with(
                            partner.genome, mutation_rate=0.025
                        )

                        # Spawn near midpoint, biased toward initiator
                        cx = (2 * initiator.x + partner.x) // 3
                        cy = (2 * initiator.y + partner.y) // 3
                        child = Walker(cx % width, cy % height, genome=child_genome)
                        spawner.add(child)

                # Remove aged/weak walkers; repopulate from survivors
                spawner.remove_dead(max_age=700, vigor_threshold=0.05)
                while not spawner.is_full() and len(spawner.walkers) >= 2:
                    p1, p2 = random.sample(spawner.walkers, 2)
                    if p1.genome.can_breed_with(p2.genome):
                        spawner.spawn_from_parents(p1, p2, mutation_rate=0.03)
                    else:
                        # Replace with a fresh walker near a random survivor
                        src = random.choice(spawner.walkers)
                        new_g = src.genome.mutate(0.04)
                        spawner.spawn_at(
                            (src.x + random.randint(-4, 4)) % width,
                            (src.y + random.randint(-4, 4)) % height,
                            genome=new_g
                        )
                    if len(spawner.walkers) >= spawner.max_walkers:
                        break

                scent.update()
                territory.update()
                active_ids = {id(w) for w in spawner.walkers}
                territory.prune_genomes(active_ids)

                # ── render ─────────────────────────────────────────────────
                stage.clear()

                # Background: territory colours
                terr_render = territory.render()
                for y in range(height):
                    for x in range(width):
                        char, fg, bg = terr_render[y][x]
                        stage.cells[y][x].char     = char
                        stage.cells[y][x].fg_color = fg
                        stage.cells[y][x].bg_color = bg

                # Foreground: walkers coloured by quaternion genome
                for walker in spawner.walkers:
                    wx, wy = walker.x, walker.y
                    if 0 <= wx < width and 0 <= wy < height:
                        r, g, b = walker.genome.to_rgb()
                        # Boost brightness by affinity
                        boost = affinity_boost(walker.genome)
                        r = min(255, int(r * boost))
                        g = min(255, int(g * boost))
                        b = min(255, int(b * boost))
                        stage.cells[wy][wx].char     = affinity_char(walker.genome)
                        stage.cells[wy][wx].fg_color = (r, g, b)

                # ── status line ────────────────────────────────────────────
                stats = spawner.get_stats()
                lin_l, lin_r = seam_stats(spawner, width)
                avg_aff = (
                    sum(w.genome.resonance_affinity for w in spawner.walkers)
                    / max(1, len(spawner.walkers))
                )

                status = (
                    f"tick {tick:6d} | "
                    f"pop {stats['count']:3d} | "
                    f"affinity {avg_aff:.3f} | "
                    f"cross L→R {lin_l:.1%} | "
                    f"cross R→L {lin_r:.1%} | "
                    f"age {stats['avg_age']:.0f}"
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
