#!/usr/bin/env python3
"""
three_nodes.py — Three populations, three islands, migration as comma

MOTIVATION
----------
The wolf_interval probe showed that the gap requires spatial locality —
the comma alone produces uniform drift, but uneven encounter density
creates holes. This sketch asks: what if we make the spatial locality
*physical*, not simulated?

Three populations occupy three "islands" (left, center, right thirds of
the screen). Each island tunes internally via Pythagorean fifths.
Occasionally a walker emigrates to an adjacent island.

The migration rate is the key parameter:
  low  → three independent commas, three independent wolves (fast)
  mid  → commas start to synchronize; wolf positions converge or diverge
  high → near one population; comma slows to single-island rate

HYPOTHESIS (to test with eyes, not logic)
-----------------------------------------
At intermediate migration rates, the three wolf gaps will not align.
Each island accumulates the comma at a slightly different phase because
each starts with a different random seed. The seams between islands —
where migrants arrive from a different comma-phase — will be visible as
regions of anomalous density: either more crowded (the meeting of two
slightly-offset distributions) or more empty (destructive interference).

The seam IS the spatial comma.

This connects to quaternion_coupling: asymmetric crossings.
A walker from the left island arriving right carries left-island comma
phase. The child they breed inherits a mix. The gradient across the
seam is the record of migration history.

NEXT STEP
---------
Run this on three actual nodes (pi-one, pi-two, pi-three) with walkers
migrating via shared state (a small Redis or even a plain file). Then
the migration latency is PHYSICAL — determined by the network — not
a probability. The seam encodes the cluster's topology.

Usage:
  python3 sketches/three_nodes.py
  python3 sketches/three_nodes.py --migration 0.002 --walkers 240
"""

import sys, os, math, time, random, argparse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.automata import Walker, Spawner, RandomWalk
from src.genetics import Genome
from src.genetics.genome import circular_mean, circular_distance
from src.renderers.terminal_stage import TerminalStage
import colorsys

PYTHAGOREAN_FIFTH = math.log2(1.5)
FIFTH_TOLERANCE   = 0.04
SPATIAL_RADIUS    = 8.0


def find_fifth_partner(walker, walkers, radius):
    target_h = (walker.genome.color_h + PYTHAGOREAN_FIFTH) % 1.0
    best, best_sdist = None, float('inf')
    for other in walkers:
        if other is walker: continue
        sdist = walker.distance_to(other)
        if sdist > radius: continue
        hdist = circular_distance(other.genome.color_h, target_h)
        if hdist < FIFTH_TOLERANCE and sdist < best_sdist:
            best, best_sdist = other, sdist
    return best


def wolf_frac(walkers, n_bins=12):
    if not walkers: return 1.0, -1
    bins = [0] * n_bins
    for w in walkers: bins[int(w.genome.color_h * n_bins) % n_bins] += 1
    expected = len(walkers) / n_bins
    min_bin = min(range(n_bins), key=lambda i: bins[i])
    return bins[min_bin] / expected if expected > 0 else 1.0, min_bin


def walker_rgb(walker):
    r, g, b = colorsys.hsv_to_rgb(walker.genome.color_h, 0.85, 0.9)
    return int(r*255), int(g*255), int(b*255)


def main():
    parser = argparse.ArgumentParser(description="Three-node island migration experiment")
    parser.add_argument('--walkers', type=int, default=210,
                        help='Total walkers, split across 3 islands (default 210)')
    parser.add_argument('--migration', type=float, default=0.003,
                        help='Per-tick probability a walker emigrates (default 0.003)')
    parser.add_argument('--tune-rate', type=float, default=0.0008)
    parser.add_argument('--delay', type=float, default=0.04)
    parser.add_argument('--seed', type=int, default=None)
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    rw = RandomWalk(eight_way=True)

    with TerminalStage() as stage:
        w, h = stage.width, stage.height
        third = w // 3

        # Three island boundaries: [0,third), [third,2*third), [2*third,w)
        islands = [
            (0,         third),
            (third,     2 * third),
            (2 * third, w),
        ]

        # Each island starts with a different base hue — spread around wheel
        spawner = Spawner(max_walkers=args.walkers, width=w, height=h)

        per_island = args.walkers // 3
        for idx, (x0, x1) in enumerate(islands):
            base_hue = idx / 3.0
            for _ in range(per_island):
                hue = (base_hue + random.gauss(0, 0.04)) % 1.0
                genome = Genome(color_h=hue, vigor=random.uniform(0.8, 1.2))
                x = random.randint(x0, x1 - 1)
                y = random.randint(0, h - 1)
                walker = Walker(x, y, genome=genome)
                spawner.add(walker)

        tick = 0
        start_means = [
            circular_mean([w.genome.color_h for w in spawner.walkers
                           if islands[i][0] <= w.x < islands[i][1]])
            for i in range(3)
        ]

        try:
            while True:
                spawner.age_all()

                for walker in list(spawner.walkers):
                    partner = find_fifth_partner(walker, spawner.walkers,
                                                 SPATIAL_RADIUS)
                    if partner is not None:
                        walker.genome.tune_toward(partner.genome,
                                                  rate=args.tune_rate)
                        dx = 1 if partner.x > walker.x else (-1 if partner.x < walker.x else 0)
                        dy = 1 if partner.y > walker.y else (-1 if partner.y < walker.y else 0)
                    else:
                        dx, dy = rw.get_move(walker.x, walker.y)

                    # Migration: occasionally slip into adjacent island
                    if random.random() < args.migration:
                        # Find which island we're in
                        for i, (x0, x1) in enumerate(islands):
                            if x0 <= walker.x < x1:
                                # Move to a random adjacent island
                                neighbors = [j for j in (i-1, i+1) if 0 <= j < 3]
                                if neighbors:
                                    dest = random.choice(neighbors)
                                    dx0, dx1 = islands[dest]
                                    walker.x = random.randint(dx0, dx1 - 1)
                                    walker.y = random.randint(0, h - 1)
                                break
                    else:
                        # Normal move, constrained to current island
                        for x0, x1 in islands:
                            if x0 <= walker.x < x1:
                                new_x = walker.x + dx
                                # Soft wall: don't cross island boundary unless migrating
                                if x0 <= new_x < x1:
                                    walker.move(dx, dy, w, h, wrap=False)
                                else:
                                    walker.move(0, dy, w, h, wrap=False)
                                break

                # Cull and repopulate
                spawner.remove_dead(max_age=800, vigor_threshold=0.05)
                while not spawner.is_full() and len(spawner.walkers) >= 2:
                    p1, p2 = random.sample(spawner.walkers, 2)
                    spawner.spawn_from_parents(p1, p2, mutation_rate=0.02)

                # Render
                stage.clear()
                for walker in spawner.walkers:
                    wx, wy = walker.x, walker.y
                    if 0 <= wx < w and 0 <= wy < h:
                        r, g, b = walker_rgb(walker)
                        stage.cells[wy][wx].fg_color = (r, g, b)
                        stage.cells[wy][wx].char = '●'

                # Draw island dividers
                for div_x in [third, 2 * third]:
                    for row in range(h):
                        stage.cells[row][div_x].char = '│'
                        stage.cells[row][div_x].fg_color = (80, 80, 80)

                # Status: per-island drift
                island_walkers = [
                    [wal for wal in spawner.walkers
                     if islands[i][0] <= wal.x < islands[i][1]]
                    for i in range(3)
                ]
                drifts = []
                wolves = []
                for i, iw in enumerate(island_walkers):
                    if iw:
                        m = circular_mean([wal.genome.color_h for wal in iw])
                        d = ((m - start_means[i]) % 1.0)
                        if d > 0.5: d -= 1.0
                        drifts.append(d * 1200)
                        wf, wb = wolf_frac(iw)
                        wolves.append(f"w{i}:{wf:.0%}")
                    else:
                        drifts.append(0.0)
                        wolves.append(f"w{i}:--")

                status = (
                    f"tick {tick:5d} | "
                    f"drift L{drifts[0]:+.0f}¢ C{drifts[1]:+.0f}¢ R{drifts[2]:+.0f}¢ | "
                    f"pop {len(spawner.walkers)} | "
                    f"{' '.join(wolves)} | "
                    f"migration={args.migration:.3f}"
                )

                stage.render_diff()
                sys.stdout.write(f"\x1b[{h+1};1H{status}\x1b[K")
                sys.stdout.flush()

                time.sleep(args.delay)
                tick += 1

        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
