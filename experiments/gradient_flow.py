#!/usr/bin/env python3
"""
gradient_flow.py - Pure aesthetic: flowing color gradients

Demonstrates:
- Emergent color gradients from memetic flow
- No competition or death - pure beauty
- Walkers reproduce and drift through color space
- Territory creates smooth color transitions

This is the "screensaver mode" - mesmerizing to watch.

Key mechanics:
- Walkers leave trails and claim territory
- Reproduction blends parent colors with drift
- No death (population stays at max)
- Event system adds color waves and shifts

Expected patterns:
- Smooth color gradients across screen
- Flowing waves of color
- Occasional bursts that create new patterns
- Hypnotic, meditative motion
"""

import sys
import os
import time
import random
import argparse

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.automata import Walker, Spawner, RandomWalk, BiasedWalk
from src.genetics import Genome
from src.fields import DiffusionField, TerritoryField
from src.events import (
    EventScheduler,
    PeriodicEventSpawner,
    GlobalColorShift,
    VigorWave,
    FieldPulse
)
from src.renderers.terminal_stage import TerminalStage


def main():
    parser = argparse.ArgumentParser(description="Gradient Flow - Aesthetic Mode")
    parser.add_argument('--walkers', type=int, default=250,
                       help='Number of walkers (stays constant)')
    parser.add_argument('--spawn-rate', type=float, default=0.15,
                       help='Reproduction rate (high for constant flux)')
    parser.add_argument('--mutation-rate', type=float, default=0.05,
                       help='Color drift rate (higher = more rainbow)')
    parser.add_argument('--events', action='store_true',
                       help='Enable color shift events')
    parser.add_argument('--delay', type=float, default=0.03,
                       help='Frame delay')
    parser.add_argument('--seed', type=int, default=None)
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    with TerminalStage() as stage:
        width, height = stage.width, stage.height

        # Components
        spawner = Spawner(max_walkers=args.walkers, width=width, height=height)
        scent = DiffusionField(width, height, diffusion_rate=0.3, decay_rate=0.88)
        territory = TerritoryField(width, height, chunk_size=6)

        # Movement: Mostly random with occasional drift
        random_walk = RandomWalk(eight_way=True)

        # Spawn initial walkers with rainbow distribution
        for i in range(args.walkers):
            hue = i / args.walkers  # Even distribution across hue wheel
            genome = Genome(
                color_h=hue,
                vigor=random.uniform(0.8, 1.2),
                saturation=random.uniform(0.7, 0.95),
                value=random.uniform(0.8, 0.95)
            )
            spawner.spawn_random(genome=genome, char='·')

        # Event system (optional)
        event_scheduler = None
        periodic_spawner = None

        if args.events:
            event_scheduler = EventScheduler()

            # Custom aesthetic event pool
            aesthetic_events = [
                lambda: GlobalColorShift(
                    duration=random.randint(100, 300),
                    shift_rate=random.uniform(0.002, 0.01)
                ),
                lambda: VigorWave(
                    duration=random.randint(80, 200),
                    amplitude=random.uniform(0.1, 0.3)
                ),
                lambda: FieldPulse(
                    duration=30,
                    x=random.randint(0, width-1),
                    y=random.randint(0, height-1),
                    strength=random.uniform(8.0, 20.0)
                ),
            ]

            periodic_spawner = PeriodicEventSpawner(
                event_scheduler,
                aesthetic_events,
                interval_range=(150, 400)
            )

            system = {
                'spawner': spawner,
                'field': scent,
                'config': {
                    'spawn_rate': args.spawn_rate,
                    'mutation_rate': args.mutation_rate,
                }
            }

        tick = 0

        try:
            while True:
                # === UPDATE PHASE ===

                # No aging or death in aesthetic mode!

                # Movement and trails
                for walker in spawner.walkers:
                    # Deposit vibrant trail
                    scent.deposit(walker.x, walker.y, walker.vigor * 1.5)

                    # Claim territory
                    territory.claim(walker)

                    # Movement with occasional directional bias
                    if random.random() < 0.85:
                        dx, dy = random_walk.get_move(walker.x, walker.y)
                    else:
                        # Occasional biased drift
                        bias_dir = (random.randint(-1, 1), random.randint(-1, 1))
                        biased = BiasedWalk(bias_direction=bias_dir, bias_strength=0.7)
                        dx, dy = biased.get_move(walker.x, walker.y)

                    walker.move(dx, dy, width, height, wrap=True)

                # Reproduction: Always spawn if under capacity
                # No breeding partners needed - pure color drift
                if random.random() < args.spawn_rate:
                    if len(spawner.walkers) < args.walkers:
                        # Spawn new walker from random parent
                        parent = random.choice(spawner.walkers)
                        child_genome = parent.genome.mutate(rate=args.mutation_rate)

                        spawner.spawn_at(
                            parent.x + random.randint(-3, 3),
                            parent.y + random.randint(-3, 3),
                            genome=child_genome,
                            char='·'
                        )
                    elif spawner.walkers:
                        # At capacity: replace random walker (constant churn)
                        old_walker = random.choice(spawner.walkers)
                        parent = random.choice(spawner.walkers)

                        # Replace
                        child_genome = parent.genome.mutate(rate=args.mutation_rate)
                        old_walker.genome = child_genome
                        old_walker.x = parent.x + random.randint(-3, 3)
                        old_walker.y = parent.y + random.randint(-3, 3)
                        old_walker.vigor = child_genome.vigor

                # Update fields
                scent.update()
                territory.update()

                # Update events
                if event_scheduler:
                    event_scheduler.update(system)
                    periodic_spawner.update()

                # Clean up genome references
                active_ids = {id(w) for w in spawner.walkers}
                territory.prune_genomes(active_ids)

                # === RENDER PHASE ===

                stage.clear()

                # Layer 1: Scent field (dim background glow)
                scent_render = scent.render()
                for y in range(height):
                    for x in range(width):
                        char, fg, bg = scent_render[y][x]
                        # Very dim scent
                        stage.cells[y][x].bg_color = (bg[0]//6, bg[1]//6, bg[2]//6)

                # Layer 2: Territory (main background)
                territory_render = territory.render()
                for y in range(height):
                    for x in range(width):
                        char, fg, territory_bg = territory_render[y][x]
                        # Blend with scent
                        scent_bg = stage.cells[y][x].bg_color
                        blended_bg = (
                            (territory_bg[0] + scent_bg[0]) // 2,
                            (territory_bg[1] + scent_bg[1]) // 2,
                            (territory_bg[2] + scent_bg[2]) // 2,
                        )
                        stage.cells[y][x].bg_color = blended_bg

                # Layer 3: Walkers (foreground)
                for walker in spawner.walkers:
                    if 0 <= walker.x < width and 0 <= walker.y < height:
                        r, g, b = walker.genome.to_rgb()
                        stage.cells[walker.y][walker.x].char = '●'
                        stage.cells[walker.y][walker.x].fg_color = (r, g, b)

                # Status line
                stats = spawner.get_stats()
                event_status = ""
                if event_scheduler:
                    event_status = event_scheduler.get_status_line()

                status = (
                    f"Tick: {tick:6d} | "
                    f"Walkers: {stats['count']:3d} | "
                    f"Avg Hue: {sum(w.genome.color_h for w in spawner.walkers)/len(spawner.walkers):.3f} | "
                    f"Mutation: {args.mutation_rate:.2f} | "
                    f"{event_status}"
                )

                stage.render_diff()
                sys.stdout.write(f"\x1b[{height+1};1H{status}\x1b[K")
                sys.stdout.flush()

                time.sleep(args.delay)
                tick += 1

        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
