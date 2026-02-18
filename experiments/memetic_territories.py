#!/usr/bin/env python3
"""
memetic_territories.py - Example modular experiment

Demonstrates composition of:
- Walkers with genetic traits (src.automata)
- Memetic color genomes (src.genetics)
- Diffusion field for scent trails (src.fields)
- Territory field for ownership tracking (src.fields)
- Event system for perturbations (src.events)
- Terminal rendering (src.renderers)

This is a ~100 line experiment built from reusable components.
"""

import sys
import os
import time
import random
import argparse

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.automata import Walker, Spawner, RandomWalk, GradientFollow
from src.genetics import Genome
from src.fields import DiffusionField, TerritoryField
from src.events import EventScheduler, PeriodicEventSpawner, AESTHETIC_POOL
from src.renderers.terminal_stage import TerminalStage


def main():
    parser = argparse.ArgumentParser(description="Memetic Territory Experiment")
    parser.add_argument('--initial-walkers', type=int, default=20,
                       help='Initial population size')
    parser.add_argument('--max-walkers', type=int, default=300,
                       help='Maximum population')
    parser.add_argument('--breed-radius', type=float, default=5.0,
                       help='Breeding distance threshold')
    parser.add_argument('--spawn-rate', type=float, default=0.05,
                       help='Probability of spawning per tick')
    parser.add_argument('--delay', type=float, default=0.03,
                       help='Delay between frames (seconds)')
    parser.add_argument('--events', action='store_true',
                       help='Enable perturbative events')
    parser.add_argument('--seed', type=int, default=None,
                       help='Random seed')
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    # Initialize terminal
    with TerminalStage() as stage:
        width, height = stage.width, stage.height

        # Create components
        spawner = Spawner(max_walkers=args.max_walkers, width=width, height=height)
        scent_field = DiffusionField(width, height, diffusion_rate=0.2, decay_rate=0.95)
        territory_field = TerritoryField(width, height, chunk_size=8)

        # Initialize walkers
        for _ in range(args.initial_walkers):
            genome = Genome(
                color_h=random.random(),
                vigor=random.uniform(0.7, 1.3)
            )
            spawner.spawn_random(genome=genome, char='·')

        # Event system (optional)
        event_scheduler = None
        periodic_spawner = None
        if args.events:
            event_scheduler = EventScheduler()
            periodic_spawner = PeriodicEventSpawner(
                event_scheduler,
                AESTHETIC_POOL,
                interval_range=(200, 500)
            )

        # System state dict for events
        system = {
            'spawner': spawner,
            'field': scent_field,
            'config': {
                'spawn_rate': args.spawn_rate,
                'mutation_rate': 0.03,
            }
        }

        tick = 0

        try:
            while True:
                # === UPDATE PHASE ===

                # Age walkers
                spawner.age_all()

                # Walker behavior
                for walker in spawner.walkers:
                    # Deposit scent trail
                    scent_field.deposit(walker.x, walker.y, walker.vigor * 0.5)

                    # Claim territory
                    territory_field.claim(walker)

                    # Movement: Follow scent gradient with some randomness
                    if random.random() < 0.7:
                        behavior = GradientFollow('scent', attraction=True)
                        dx, dy = behavior.get_move(walker.x, walker.y, field=scent_field)
                    else:
                        behavior = RandomWalk(eight_way=True)
                        dx, dy = behavior.get_move(walker.x, walker.y)

                    walker.move(dx, dy, width, height, wrap=True)

                # Reproduction: Find nearby compatible partners
                if not spawner.is_full() and random.random() < system['config']['spawn_rate']:
                    walker = random.choice(spawner.walkers)
                    partners = spawner.find_breeding_partners(walker, args.breed_radius)
                    if partners:
                        partner = random.choice(partners)
                        spawner.spawn_from_parents(
                            walker, partner,
                            mutation_rate=system['config']['mutation_rate']
                        )

                # Remove old walkers
                spawner.remove_dead(max_age=1000, vigor_threshold=0.1)

                # Update fields
                scent_field.update()
                territory_field.update()

                # Update events
                if event_scheduler:
                    event_scheduler.update(system)
                    periodic_spawner.update()

                # Clean up stale genome references
                active_ids = {id(w) for w in spawner.walkers}
                territory_field.prune_genomes(active_ids)

                # === RENDER PHASE ===

                # Composite rendering
                stage.clear()

                # Background: Territory colors
                territory_render = territory_field.render()
                for y in range(height):
                    for x in range(width):
                        char, fg, bg = territory_render[y][x]
                        stage.cells[y][x].char = char
                        stage.cells[y][x].fg_color = fg
                        stage.cells[y][x].bg_color = bg

                # Foreground: Walkers
                for walker in spawner.walkers:
                    if 0 <= walker.x < width and 0 <= walker.y < height:
                        r, g, b = walker.genome.to_rgb()
                        stage.cells[walker.y][walker.x].char = '●'
                        stage.cells[walker.y][walker.x].fg_color = (r, g, b)

                # Status line
                stats = spawner.get_stats()
                territory_stats = territory_field.get_stats()
                event_status = event_scheduler.get_status_line() if event_scheduler else "No events"

                status = (
                    f"Tick: {tick:6d} | "
                    f"Pop: {stats['count']:3d}/{args.max_walkers} | "
                    f"Avg Age: {stats['avg_age']:.1f} | "
                    f"Avg Vigor: {stats['avg_vigor']:.2f} | "
                    f"Territory: {territory_stats['coverage']:.1%} | "
                    f"{event_status}"
                )

                # Render to terminal
                stage.render_diff()
                sys.stdout.write(f"\x1b[{height+1};1H{status}\x1b[K")
                sys.stdout.flush()

                time.sleep(args.delay)
                tick += 1

        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
