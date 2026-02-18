#!/usr/bin/env python3
"""
simple_walkers.py - Minimal modular experiment

Bare minimum example: Just walkers with colors, no fields or events.
Demonstrates how little code is needed with modular components.
"""

import sys
import os
import time
import random
import argparse

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.automata import Walker, Spawner, RandomWalk
from src.genetics import Genome


def render_simple(walkers, width, height):
    """Simple ASCII rendering without TerminalStage"""
    grid = [[' ' for _ in range(width)] for _ in range(height)]

    for walker in walkers:
        if 0 <= walker.x < width and 0 <= walker.y < height:
            grid[walker.y][walker.x] = '●'

    # Clear and render
    sys.stdout.write('\x1b[2J\x1b[H')  # Clear screen, move to home
    for row in grid:
        sys.stdout.write(''.join(row) + '\n')
    sys.stdout.flush()


def main():
    parser = argparse.ArgumentParser(description="Simple Walker Experiment")
    parser.add_argument('--walkers', type=int, default=50)
    parser.add_argument('--width', type=int, default=80)
    parser.add_argument('--height', type=int, default=24)
    parser.add_argument('--delay', type=float, default=0.05)
    args = parser.parse_args()

    # Create spawner
    spawner = Spawner(max_walkers=args.walkers, width=args.width, height=args.height)

    # Spawn initial population
    for _ in range(args.walkers):
        genome = Genome(color_h=random.random())
        spawner.spawn_random(genome=genome)

    # Movement behavior
    behavior = RandomWalk(eight_way=True)

    try:
        while True:
            # Move all walkers
            for walker in spawner.walkers:
                dx, dy = behavior.get_move(walker.x, walker.y)
                walker.move(dx, dy, args.width, args.height, wrap=True)

            # Render
            render_simple(spawner.walkers, args.width, args.height)

            # Stats
            stats = spawner.get_stats()
            sys.stdout.write(f"Population: {stats['count']} | Avg Age: {stats['avg_age']:.1f}\n")

            time.sleep(args.delay)

            # Age walkers
            spawner.age_all()

    except KeyboardInterrupt:
        sys.stdout.write('\x1b[?25h')  # Show cursor
        pass


if __name__ == '__main__':
    main()
