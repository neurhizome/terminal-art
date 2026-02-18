#!/usr/bin/env python3
"""
Quick sketch runner with presets

Usage:
    python3 -m sketches meditative
    python3 -m sketches chaotic --walkers 500
    python3 -m sketches aesthetic --seed 42
"""

import sys
import os
import argparse

# Add parent to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.sketchbook import preset, PRESETS


def main():
    parser = argparse.ArgumentParser(
        description="Quick sketch runner",
        epilog=f"Available presets: {', '.join(PRESETS.keys())}"
    )
    parser.add_argument('preset', choices=PRESETS.keys(), help='Preset to run')
    parser.add_argument('--walkers', type=int, help='Override number of walkers')
    parser.add_argument('--seed', type=int, help='Random seed')
    parser.add_argument('--delay', type=float, help='Frame delay')
    parser.add_argument('--no-events', action='store_true', help='Disable events')

    args = parser.parse_args()

    # Build overrides
    overrides = {}
    if args.walkers:
        overrides['n_walkers'] = args.walkers
    if args.seed is not None:
        overrides['seed'] = args.seed
    if args.delay:
        overrides['delay'] = args.delay
    if args.no_events:
        overrides['events'] = False

    # Run preset
    print(f"Running preset: {args.preset}")
    if overrides:
        print(f"Overrides: {overrides}")
    print("Press Ctrl-C to exit\n")

    sketch = preset(args.preset, **overrides)
    sketch.run()


if __name__ == '__main__':
    main()
