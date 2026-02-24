#!/usr/bin/env python3
"""
recaman_arcs.py - The Recamán sequence drawn as nested arcs

OEIS A005132 — the Recamán sequence:
    a(0) = 0
    a(n) = a(n-1) - n   if that value is positive and not yet in the sequence
    a(n) = a(n-1) + n   otherwise

The sequence begins: 0, 1, 3, 6, 2, 7, 13, 20, 12, 21, 11, 22, 10, 23 ...

Notice the characteristic behaviour: it leaps forward in large steps, then
doubles back to fill gaps it skipped. Every positive integer is believed to
appear eventually (unproved). The path to get there is never direct.

Visualisation: each consecutive pair (a[n], a[n+1]) is connected by a
semicircular arc above or below a central number line. Arcs alternate
sides. The result is a topological tangle — nested loops, crossings,
the record of a sequence that cannot decide which way to go.

Colours cycle through the rainbow as the sequence progresses. Arcs are
traced with Unicode box-drawing characters (╭─╮ / ╰─╯).

Usage:
    python3 demos/recaman_arcs.py
    python3 demos/recaman_arcs.py --terms 40
    python3 demos/recaman_arcs.py --terms 20 --static
    python3 demos/recaman_arcs.py --no-color
"""

import sys
import math
import time
import shutil
import argparse


# ---------------------------------------------------------------------------
# Colour helpers
# ---------------------------------------------------------------------------

def _hsv_to_rgb(h: float, s: float = 0.8, v: float = 0.9):
    """h in [0, 1). Returns (r, g, b) ints 0-255."""
    h6 = h * 6.0
    i  = int(h6)
    f  = h6 - i
    p  = v * (1.0 - s)
    q  = v * (1.0 - f * s)
    t  = v * (1.0 - (1.0 - f) * s)
    sectors = [(v, t, p), (q, v, p), (p, v, t),
               (p, q, v), (t, p, v), (v, p, q)]
    r, g, b = sectors[i % 6]
    return int(r * 255), int(g * 255), int(b * 255)


def _fg(r: int, g: int, b: int) -> str:
    return f'\x1b[38;2;{r};{g};{b}m'

RESET   = '\x1b[0m'
DIM_GREY = _fg(70, 70, 70)


# ---------------------------------------------------------------------------
# Sequence
# ---------------------------------------------------------------------------

def recaman(n_terms: int) -> list:
    """Return the first n_terms of the Recamán sequence."""
    seq  = [0]
    seen = {0}
    for n in range(1, n_terms):
        backward = seq[-1] - n
        if backward > 0 and backward not in seen:
            seq.append(backward)
        else:
            seq.append(seq[-1] + n)
        seen.add(seq[-1])
    return seq


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def build_grid(width: int, height: int,
               seq: list, n_arcs: int,
               x_scale: float, x_offset: float,
               color_shift: float, use_color: bool):
    """
    Render Recamán arcs into a width×height character grid.

    Returns a list-of-lists of (char, ansi_prefix) pairs.
    """
    # Grid cells: (char, color_str)
    blank = (' ', '')
    grid  = [[blank] * width for _ in range(height)]

    def plot(px: int, py: int, char: str, color: str):
        if 0 <= px < width and 0 <= py < height:
            grid[py][px] = (char, color)

    center_y = height // 2

    # Central axis
    axis_color = DIM_GREY if use_color else ''
    for px in range(width):
        plot(px, center_y, '─', axis_color)

    for i in range(min(n_arcs, len(seq) - 1)):
        x1, x2 = seq[i], seq[i + 1]
        px1 = int(x1 * x_scale + x_offset)
        px2 = int(x2 * x_scale + x_offset)

        if px1 == px2:
            continue

        above = (i % 2 == 0)
        lo, hi = min(px1, px2), max(px1, px2)

        # Colour: hue based on arc index, animated by color_shift
        hue = ((i / max(n_arcs, 1)) * 0.85 + color_shift) % 1.0
        r, g, b = _hsv_to_rgb(hue)
        color = _fg(r, g, b) if use_color else ''

        # Parabolic arc over [lo, hi]
        cx     = (px1 + px2) / 2.0
        radius = (hi - lo) / 2.0

        for px in range(lo, hi + 1):
            t = (px - cx) / radius if radius > 0 else 0.0
            t = max(-1.0, min(1.0, t))
            y_frac = math.sqrt(max(0.0, 1.0 - t * t))

            # Terminal aspect: characters are ~2× taller than wide
            arc_h = max(1, int(radius * y_frac * 0.45))
            py    = (center_y - arc_h) if above else (center_y + arc_h)

            # Choose horizontal-ish box-drawing characters
            if above:
                if   t < -0.75: char = '╭'
                elif t >  0.75: char = '╮'
                else:           char = '─'
            else:
                if   t < -0.75: char = '╰'
                elif t >  0.75: char = '╯'
                else:           char = '─'

            plot(px, py, char, color)

        # Mark both endpoints on the axis
        for px in (px1, px2):
            plot(px, center_y, '●', color)

    return grid


def render(grid, width: int, height: int):
    """Flush the grid to stdout."""
    rows = []
    for row in range(height - 1):
        cells = []
        prev_color = None
        for col in range(width):
            char, color = grid[row][col]
            if color != prev_color:
                cells.append(color if color else RESET)
                prev_color = color
            cells.append(char)
        rows.append(''.join(cells))
    sys.stdout.write('\x1b[H' + '\n'.join(rows) + RESET)
    sys.stdout.flush()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Recamán sequence — nested arc visualisation'
    )
    parser.add_argument('--terms', type=int, default=32,
                        help='Number of Recamán terms / arcs to display')
    parser.add_argument('--delay', type=float, default=0.06,
                        help='Seconds between animation frames (colour cycling)')
    parser.add_argument('--no-color', action='store_true',
                        help='Disable ANSI colour output')
    parser.add_argument('--static', action='store_true',
                        help='Render one frame then wait for Enter')
    args = parser.parse_args()

    width, height = shutil.get_terminal_size((80, 24))
    use_color     = not args.no_color

    seq     = recaman(args.terms + 1)
    max_val = max(seq) if seq else 1

    # Fit the whole sequence across the terminal with small margins
    x_scale  = (width - 6) / max(max_val, 1)
    x_offset = 3.0

    sys.stdout.write('\x1b[?25l\x1b[2J\x1b[H')
    sys.stdout.flush()

    color_shift = 0.0

    try:
        while True:
            grid = build_grid(width, height, seq, args.terms,
                              x_scale, x_offset, color_shift, use_color)
            render(grid, width, height)

            # Status bar
            status = (
                f' Recamán  terms: {args.terms}'
                f'  max value: {max_val}'
                f'  a(n) = a(n-1)∓n  [OEIS A005132]'
                f'  ^C to quit'
            )
            sys.stdout.write(f'\x1b[{height};1H\x1b[K{status[:width - 1]}\x1b[0m')
            sys.stdout.flush()

            if args.static:
                input()
                break

            time.sleep(args.delay)
            color_shift = (color_shift + 0.004) % 1.0

    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write('\x1b[?25h\x1b[0m\n')
        sys.stdout.flush()


if __name__ == '__main__':
    main()
