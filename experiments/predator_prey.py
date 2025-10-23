#!/usr/bin/env python3
"""
predator_prey.py - Classic Lotka-Volterra dynamics in terminal space

Demonstrates:
- Two populations with asymmetric interactions
- Prey leaves scent trails while foraging
- Predators follow scent gradients to hunt
- Population oscillations (predator-prey cycles)
- Spatial patterns (prey clustering, predator dispersal)

Key mechanics:
- Prey: RandomWalk, deposits green scent
- Predators: GradientFollow prey scent, consume nearby prey
- Prey reproduces faster but dies when caught
- Predators gain vigor from eating, die if starved

Expected patterns:
- Population oscillations (classic cycles)
- Prey forms clusters for safety
- Predators patrol between clusters
- Spatial waves of predation
"""

import sys
import time
import random
import argparse
from dataclasses import dataclass
from src.automata import Walker, Spawner, RandomWalk, GradientFollow
from src.genetics import Genome
from src.fields import DiffusionField
from src.renderers.terminal_stage import TerminalStage


@dataclass
class PopulationStats:
    """Track prey and predator populations over time"""
    prey_count: int = 0
    predator_count: int = 0


def main():
    parser = argparse.ArgumentParser(description="Predator-Prey Experiment")
    parser.add_argument('--initial-prey', type=int, default=60,
                       help='Initial prey population')
    parser.add_argument('--initial-predators', type=int, default=15,
                       help='Initial predator population')
    parser.add_argument('--max-walkers', type=int, default=500,
                       help='Maximum total population')
    parser.add_argument('--prey-spawn-rate', type=float, default=0.12,
                       help='Prey reproduction rate')
    parser.add_argument('--predator-spawn-rate', type=float, default=0.03,
                       help='Predator reproduction rate')
    parser.add_argument('--hunt-radius', type=float, default=2.0,
                       help='How close predator must be to catch prey')
    parser.add_argument('--delay', type=float, default=0.03,
                       help='Delay between frames')
    parser.add_argument('--seed', type=int, default=None)
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    with TerminalStage() as stage:
        width, height = stage.width, stage.height

        # Components
        prey_spawner = Spawner(max_walkers=args.max_walkers, width=width, height=height)
        predator_spawner = Spawner(max_walkers=args.max_walkers // 3, width=width, height=height)
        prey_scent = DiffusionField(width, height, diffusion_rate=0.25, decay_rate=0.92)

        # Behaviors
        prey_behavior = RandomWalk(eight_way=True)
        predator_behavior = GradientFollow('prey_scent', attraction=True, sensitivity=1.2)

        # Spawn initial populations
        # Prey: Green
        for _ in range(args.initial_prey):
            genome = Genome(color_h=0.33, saturation=0.8, value=0.9, vigor=1.0)  # Green
            prey_spawner.spawn_random(genome=genome, char='○')

        # Predators: Red
        for _ in range(args.initial_predators):
            genome = Genome(color_h=0.0, saturation=0.9, value=0.9, vigor=1.5)  # Red
            predator_spawner.spawn_random(genome=genome, char='●')

        # Track population history
        history = []
        tick = 0

        try:
            while True:
                # === UPDATE PHASE ===

                prey_spawner.age_all()
                predator_spawner.age_all()

                # Prey movement and scent deposition
                for prey in prey_spawner.walkers:
                    # Random walk
                    dx, dy = prey_behavior.get_move(prey.x, prey.y)
                    prey.move(dx, dy, width, height, wrap=True)

                    # Leave scent trail
                    prey_scent.deposit(prey.x, prey.y, 1.0)

                # Predator movement (follow prey scent)
                for predator in predator_spawner.walkers:
                    # Follow gradient (with some randomness)
                    if random.random() < 0.8:
                        dx, dy = predator_behavior.get_move(
                            predator.x, predator.y,
                            field=prey_scent
                        )
                    else:
                        dx, dy = prey_behavior.get_move(predator.x, predator.y)

                    predator.move(dx, dy, width, height, wrap=True)

                    # Hunt: Consume nearby prey
                    nearby_prey = []
                    for prey in prey_spawner.walkers:
                        if predator.distance_to(prey) <= args.hunt_radius:
                            nearby_prey.append(prey)

                    if nearby_prey:
                        # Eat one prey
                        victim = random.choice(nearby_prey)
                        victim.die()
                        predator.modify_vigor(0.3)  # Gain energy

                    # Predators slowly lose vigor (starvation)
                    predator.modify_vigor(-0.008)

                # Prey reproduction (asexual for simplicity)
                if not prey_spawner.is_full() and random.random() < args.prey_spawn_rate:
                    if prey_spawner.walkers:
                        parent = random.choice(prey_spawner.walkers)
                        # Spawn nearby
                        child_genome = parent.genome.mutate(rate=0.01)
                        prey_spawner.spawn_at(
                            parent.x + random.randint(-2, 2),
                            parent.y + random.randint(-2, 2),
                            genome=child_genome,
                            char='○'
                        )

                # Predator reproduction (needs high vigor)
                if not predator_spawner.is_full() and random.random() < args.predator_spawn_rate:
                    healthy_predators = [p for p in predator_spawner.walkers if p.vigor > 1.5]
                    if healthy_predators:
                        parent = random.choice(healthy_predators)
                        child_genome = parent.genome.mutate(rate=0.01)
                        predator_spawner.spawn_at(
                            parent.x + random.randint(-3, 3),
                            parent.y + random.randint(-3, 3),
                            genome=child_genome,
                            char='●'
                        )
                        parent.modify_vigor(-0.5)  # Cost of reproduction

                # Death
                prey_spawner.remove_dead(max_age=600, vigor_threshold=0.1)
                predator_spawner.remove_dead(max_age=1000, vigor_threshold=0.2)

                # Update scent field
                prey_scent.update()

                # Track populations
                if tick % 10 == 0:
                    history.append(PopulationStats(
                        prey_count=len(prey_spawner.walkers),
                        predator_count=len(predator_spawner.walkers)
                    ))
                    if len(history) > 100:
                        history.pop(0)

                # === RENDER PHASE ===

                stage.clear()

                # Background: Prey scent field (subtle green glow)
                scent_render = prey_scent.render()
                for y in range(height):
                    for x in range(width):
                        char, fg, bg = scent_render[y][x]
                        # Dim the scent visualization
                        stage.cells[y][x].bg_color = (bg[0]//4, bg[1]//4, bg[2]//4)

                # Foreground: Prey (green circles)
                for prey in prey_spawner.walkers:
                    if 0 <= prey.x < width and 0 <= prey.y < height:
                        r, g, b = prey.genome.to_rgb()
                        stage.cells[prey.y][prey.x].char = '○'
                        stage.cells[prey.y][prey.x].fg_color = (r, g, b)

                # Foreground: Predators (red dots, on top)
                for predator in predator_spawner.walkers:
                    if 0 <= predator.x < width and 0 <= predator.y < height:
                        r, g, b = predator.genome.to_rgb()
                        stage.cells[predator.y][predator.x].char = '●'
                        stage.cells[predator.y][predator.x].fg_color = (r, g, b)

                # Status line with population trend
                prey_stats = prey_spawner.get_stats()
                pred_stats = predator_spawner.get_stats()

                # Simple trend indicator
                if len(history) >= 2:
                    prey_trend = "↑" if history[-1].prey_count > history[-2].prey_count else "↓"
                    pred_trend = "↑" if history[-1].predator_count > history[-2].predator_count else "↓"
                else:
                    prey_trend = pred_trend = "→"

                status = (
                    f"Tick: {tick:6d} | "
                    f"Prey: {prey_stats['count']:3d} {prey_trend} "
                    f"(avg vigor: {prey_stats['avg_vigor']:.2f}) | "
                    f"Predators: {pred_stats['count']:3d} {pred_trend} "
                    f"(avg vigor: {pred_stats['avg_vigor']:.2f}) | "
                    f"Kills: {prey_spawner.total_deaths}"
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
