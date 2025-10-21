#!/usr/bin/env python3
# dots_merge.py
# Dusty's color river: terminal-width aware, stochastic neighbor merging, 24-bit ANSI colors.
# Usage: python3 dots_merge.py [--rows N] [--delay SECONDS] [--jitter 0..255] [--seed INT]
# Example: python3 dots_merge.py --rows 1000 --delay 0.02

import argparse
import random
import shutil
import sys
import time
from dataclasses import dataclass
from typing import Tuple, List

GLYPHS = ["┏", "┓", "┛", "┗"]

def clamp(x: int) -> int:
    if x < 0: return 0
    if x > 255: return 255
    return x

def random_color() -> Tuple[int, int, int]:
    return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

@dataclass
class Dot:
    fg: Tuple[int, int, int]
    bg: Tuple[int, int, int]
    glyph_idx: int = 0

    def next_glyph_idx(self) -> int:
        return (self.glyph_idx + 1) % len(GLYPHS)

    def render(self) -> str:
        r, g, b = self.fg
        br, bgc, bb = self.bg
        # 24-bit (True Color) ANSI: set FG then BG
        return f"\x1b[38;2;{r};{g};{b}m\x1b[48;2;{br};{bgc};{bb}m{GLYPHS[self.glyph_idx]}\x1b[0m"

def weighted_merge(c0: Tuple[int,int,int],
                   c1: Tuple[int,int,int],
                   c2: Tuple[int,int,int],
                   jitter: int) -> Tuple[int,int,int]:
    # Draw symmetric random weights (Dirichlet(1,1,1) via normalized uniforms)
    a, b, c = random.random(), random.random(), random.random()
    s = a + b + c
    w0, w1, w2 = a/s, b/s, c/s
    r = int(w0*c0[0] + w1*c1[0] + w2*c2[0])
    g = int(w0*c0[1] + w1*c1[1] + w2*c2[1])
    bch = int(w0*c0[2] + w1*c1[2] + w2*c2[2])
    if jitter > 0:
        r = clamp(r + random.randint(-jitter, jitter))
        g = clamp(g + random.randint(-jitter, jitter))
        bch = clamp(bch + random.randint(-jitter, jitter))
    return (r, g, bch)

def ensure_width(row: List[Dot], width: int) -> List[Dot]:
    # Expand or shrink the row to match terminal width.
    n = len(row)
    if width == n:
        return row
    if width < n:
        return row[:width]
    # width > n: append random Dots to the right
    extra = [Dot(random_color(), random_color(), random.randrange(len(GLYPHS))) for _ in range(width - n)]
    return row + extra

def make_initial_row(width: int) -> List[Dot]:
    return [Dot(random_color(), random_color(), random.randrange(len(GLYPHS))) for _ in range(width)]

def next_row(prev: List[Dot], jitter: int) -> List[Dot]:
    n = len(prev)
    out = []
    for i in range(n):
        left = prev[(i - 1) % n]
        selfd = prev[i]
        right = prev[(i + 1) % n]

        # Unbiased merge across self, right, left (weights are symmetric and freshly sampled)
        new_fg = weighted_merge(selfd.fg, right.fg, left.fg, jitter)
        new_bg = weighted_merge(selfd.bg, right.bg, left.bg, jitter)

        # Advance glyph cycle so you can watch fg/bg drift over time
        out.append(Dot(new_fg, new_bg, selfd.next_glyph_idx()))
    return out

def main():
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--rows", type=int, default=0, help="Number of lines to print (0 = infinite).")
    parser.add_argument("--delay", type=float, default=0.02, help="Seconds to sleep between lines.")
    parser.add_argument("--jitter", type=int, default=6, help="Per-step color jitter (0..255).")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility.")
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    # Make sure stdout can handle UTF-8 glyphs
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    # initial width
    width = max(1, shutil.get_terminal_size(fallback=(80, 24)).columns)
    row = make_initial_row(width)

    line_count = 0
    try:
        while True:
            # Track terminal width live so resizing works mid-run
            new_width = max(1, shutil.get_terminal_size(fallback=(80, 24)).columns)
            if new_width != width:
                width = new_width
                row = ensure_width(row, width)

             # Render and print the current row
            line = "".join(dot.render() for dot in row)
            sys.stdout.write(line + "\n")
            sys.stdout.flush()

            # Prepare next row by unbiased stochastic merging
            row = next_row(row, jitter=args.jitter)

            line_count += 1
            if args.rows and line_count >= args.rows:
                break

            if args.delay > 0:
                time.sleep(args.delay)
    except KeyboardInterrupt:
        pass
    finally:
        # Reset styles before exiting
        sys.stdout.write("\x1b[0m")
        sys.stdout.flush()

if __name__ == "__main__":
    main()
