#!/usr/bin/env python3
"""A finite, reproducible weaving with the original friend.py arithmetic.

Each row is the next state, not a frame of animation. Run from any directory:
python3 experiments/returning_thread.py --seed 23 --width 96 --half-cycle 48
"""
import argparse
from pathlib import Path
import random
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "colors" / "colorfalls"))
from friend import Dot  # Original arithmetic, including in-place neighbour reads.


def weave(seed=23, width=96, half_cycle=48, cycles=1):
    """Return ANSI rows, leaving the caller's random generator untouched."""
    state = random.getstate()
    try:
        random.seed(seed)
        dots = [Dot(i) for i in range(width)]
    finally:
        random.setstate(state)
    rows = []
    for _ in range(cycles):
        for method in ("evolve_with_neighbors", "devolve_with_neighbors"):
            for _ in range(half_cycle):
                for i, dot in enumerate(dots):
                    getattr(dot, method)(dots[(i - 1) % width],
                                         dots[(i + 1) % width], dots[width - 1 - i])
                rows.append("".join(dot.get_str() for dot in dots))
    return rows


def positive_int(value):
    value = int(value)
    if value < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=23)
    parser.add_argument("--width", type=positive_int, default=96)
    parser.add_argument("--half-cycle", type=positive_int, default=48)
    parser.add_argument("--cycles", type=positive_int, default=1)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rows = weave(args.seed, args.width, args.half_cycle, args.cycles)
    header = (f"# title: The returning thread\n# cols: {args.width}\n"
              f"# rows: {len(rows)}\n# seed: {args.seed}\n"
              f"# params: half_cycle={args.half_cycle}, cycles={args.cycles}\n"
              "# source: experiments/returning_thread.py (colors/colorfalls/friend.py)\n\n")
    # No trailing newline: preserve the first row in terminals with no scrollback.
    capture = header + "\n".join(rows)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(capture, encoding="utf-8")
        print(f"Wrote {args.output}: {args.width} columns × {len(rows)} rows")
    else:
        sys.stdout.write(capture)


if __name__ == "__main__":
    main()
