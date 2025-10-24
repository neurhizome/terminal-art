#!/usr/bin/env python3
"""
color_speciation.py - Reproductive barriers create color species

Demonstrates:
- Genetic distance-based breeding barriers
- Emergence of distinct color clusters
- Competitive exclusion between species
- Spatial segregation patterns

Key mechanic: Walkers can only breed if their hue distance < threshold.
This creates "species" of similar colors that compete for space.

Expected patterns:
- Initial diversity collapses into 3-5 dominant species
- Color boundaries form territories
- Species go extinct through competition
- Surviving species have distinct niches
"""

import sys
import os
import time
import random
import argparse

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.automata import Walker, Spawner, RandomWalk
from src.genetics import Genome, circular_distance
from src.fields import TerritoryField
from src.renderers.terminal_stage import TerminalStage


def main():
    parser = argparse.ArgumentParser(description="Color Speciation Experiment")
    parser.add_argument('--initial-species', type=int, default=8,
                       help='Number of initial color species')
    parser.add_argument('--walkers-per-species', type=int, default=15,
                       help='Initial walkers per species')
    parser.add_argument('--max-walkers', type=int, default=400,
                       help='Maximum population')
    parser.add_argument('--breed-threshold', type=float, default=0.15,
                       help='Max genetic distance for breeding (0-0.5)')
    parser.add_argument('--breed-radius', type=float, default=6.0,
                       help='Spatial distance for breeding')
    parser.add_argument('--spawn-rate', type=float, default=0.08,
                       help='Reproduction probability per tick')
    parser.add_argument('--delay', type=float, default=0.03,
                       help='Delay between frames')
    parser.add_argument('--seed', type=int, default=None,
                       help='Random seed')
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    with TerminalStage() as stage:
        width, height = stage.width, stage.height

        # Components
        spawner = Spawner(max_walkers=args.max_walkers, width=width, height=height)
        territory = TerritoryField(width, height, chunk_size=8)
        behavior = RandomWalk(eight_way=True)

        # Seed initial species (evenly spaced hues)
        for i in range(args.initial_species):
            base_hue = i / args.initial_species

            for _ in range(args.walkers_per_species):
                # Small variation within species
                hue = (base_hue + random.gauss(0, 0.02)) % 1.0
                genome = Genome(
                    color_h=hue,
                    vigor=random.uniform(0.8, 1.2),
                    saturation=0.9,
                    value=0.9
                )
                spawner.spawn_random(genome=genome, char='●')

        # Track species diversity over time
        diversity_history = []
        tick = 0

        try:
            while True:
                # === UPDATE PHASE ===

                spawner.age_all()

                # Movement and territory
                for walker in spawner.walkers:
                    territory.claim(walker)
                    dx, dy = behavior.get_move(walker.x, walker.y)
                    walker.move(dx, dy, width, height, wrap=True)

                # Reproduction with breeding barriers
                if not spawner.is_full() and random.random() < args.spawn_rate:
                    walker = random.choice(spawner.walkers)

                    # Find compatible partners (genetic + spatial proximity)
                    partners = spawner.find_breeding_partners(
                        walker,
                        args.breed_radius,
                        threshold=args.breed_threshold
                    )

                    if partners:
                        partner = random.choice(partners)
                        spawner.spawn_from_parents(walker, partner, mutation_rate=0.02)

                # Death: old age or low vigor
                spawner.remove_dead(max_age=800, vigor_threshold=0.2)

                # Clean up genome references
                active_ids = {id(w) for w in spawner.walkers}
                territory.prune_genomes(active_ids)

                # Measure diversity (number of distinct color clusters)
                if tick % 50 == 0:
                    diversity = measure_diversity(spawner.walkers)
                    diversity_history.append(diversity)
                    if len(diversity_history) > 20:
                        diversity_history.pop(0)

                # === RENDER PHASE ===

                stage.clear()

                # Background: Territory
                territory_render = territory.render()
                for y in range(height):
                    for x in range(width):
                        char, fg, bg = territory_render[y][x]
                        stage.cells[y][x].bg_color = bg

                # Foreground: Walkers
                for walker in spawner.walkers:
                    if 0 <= walker.x < width and 0 <= walker.y < height:
                        r, g, b = walker.genome.to_rgb()
                        stage.cells[walker.y][walker.x].char = '●'
                        stage.cells[walker.y][walker.x].fg_color = (r, g, b)

                # Status line
                stats = spawner.get_stats()
                current_diversity = diversity_history[-1] if diversity_history else 0
                avg_diversity = sum(diversity_history) / len(diversity_history) if diversity_history else 0

                status = (
                    f"Tick: {tick:6d} | "
                    f"Pop: {stats['count']:3d}/{args.max_walkers} | "
                    f"Species: ~{current_diversity:.1f} | "
                    f"Avg Species (1000t): {avg_diversity:.1f} | "
                    f"Breed Threshold: {args.breed_threshold:.2f} | "
                    f"Total Born: {spawner.total_spawned} Dead: {spawner.total_deaths}"
                )

                stage.render_diff()
                sys.stdout.write(f"\x1b[{height+1};1H{status}\x1b[K")
                sys.stdout.flush()

                time.sleep(args.delay)
                tick += 1

        except KeyboardInterrupt:
            pass


def measure_diversity(walkers):
    """
    Estimate number of distinct color species using simple clustering.
    Count walkers as same species if hue distance < 0.1
    """
    if not walkers:
        return 0

    hues = [w.genome.color_h for w in walkers]
    hues.sort()

    # Count clusters
    species_count = 1
    prev_hue = hues[0]

    for hue in hues[1:]:
        dist = circular_distance(prev_hue, hue)
        if dist > 0.1:  # New species
            species_count += 1
        prev_hue = hue

    # Handle wrap-around (last to first)
    if len(hues) > 1:
        wrap_dist = circular_distance(hues[-1], hues[0])
        if wrap_dist < 0.1:
            species_count -= 1  # They're the same species

    return species_count


if __name__ == '__main__':
    main()
