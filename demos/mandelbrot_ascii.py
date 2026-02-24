#!/usr/bin/env python3
"""
mandelbrot_ascii.py - The Mandelbrot set rendered in Unicode density gradients

For every point c in the complex plane, iterate z = z² + c starting from z = 0.
Count iterations until |z| > 2 (escape) or max_iter is reached.

That count — the "escape time" — is mapped to a character from a density
palette. Points that never escape form the set's interior (rendered dark).
Points that escape quickly become sparse symbols. The boundary, where escape
time diverges to infinity, is where all the complexity lives.

The set is infinitely detailed. Zoom into any boundary region and find the
same structure at every scale.

Usage:
    python3 demos/mandelbrot_ascii.py
    python3 demos/mandelbrot_ascii.py --zoom-to -0.7269,0.1889
    python3 demos/mandelbrot_ascii.py --palette classic --static
    python3 demos/mandelbrot_ascii.py --cx -0.5557 --cy 0.6395 --zoom 0.8

Palette choices: unicode (default), classic, blocks, sparse
"""

import sys
import os
import time
import math
import shutil
import argparse


# ---------------------------------------------------------------------------
# Character palettes: ordered dense → sparse (high iteration → low iteration)
# ---------------------------------------------------------------------------

PALETTE_UNICODE  = '█▓▒░·∘ '
PALETTE_CLASSIC  = '@%#*+=-:. '
PALETTE_BLOCKS   = '▉▊▋▌▍▎▏ '
PALETTE_SPARSE   = '⣿⣶⣤⡀⠀ '

# ANSI helpers

def _color(r: int, g: int, b: int) -> str:
    return f'\x1b[38;2;{r};{g};{b}m'

RESET = '\x1b[0m'


# ---------------------------------------------------------------------------
# Core math
# ---------------------------------------------------------------------------

def mandelbrot(cx: float, cy: float, max_iter: int):
    """
    Iterate z = z² + c. Return (raw_count, smooth_count).

    smooth_count uses the "continuous / normalized" coloring formula so that
    palette transitions don't show discrete banding.
    """
    zx = zy = 0.0
    for i in range(max_iter):
        zx2, zy2 = zx * zx, zy * zy
        if zx2 + zy2 > 4.0:
            # Smooth escape: log(log(|z|)) normalisation
            log_zn = math.log(zx2 + zy2) / 2.0
            nu     = math.log(log_zn / math.log(2.0)) / math.log(2.0)
            return i, i + 1.0 - nu
        zx, zy = zx2 - zy2 + cx, 2.0 * zx * zy + cy
    return max_iter, float(max_iter)


def _hsv_to_rgb(h: float, s: float = 0.85, v: float = 0.95):
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


def escape_to_color(smooth: float, max_iter: int, hue_offset: float = 0.0):
    """Map smooth iteration count to an RGB colour."""
    if smooth >= max_iter:
        return (5, 5, 15)          # Deep interior: near-black blue

    t = smooth / max_iter
    # Cycle hue, pull brightness up near the boundary
    hue = (t * 2.5 + hue_offset) % 1.0
    sat = 0.9
    val = 0.3 + 0.7 * math.sin(t * math.pi)
    return _hsv_to_rgb(hue, sat, val)


def escape_to_char(smooth: float, max_iter: int, palette: str) -> str:
    """Map smooth iteration count to a palette character."""
    if smooth >= max_iter:
        return palette[-1]         # Interior → darkest / space
    t = smooth / max_iter
    idx = int(t * (len(palette) - 1))
    return palette[min(idx, len(palette) - 1)]


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def render_frame(
    width: int, height: int,
    cx: float, cy: float, zoom: float,
    max_iter: int,
    hue_offset: float,
    palette: str,
):
    """Write one complete frame to stdout."""
    # Terminal cells are roughly twice as tall as wide — compensate
    aspect = 2.1

    rows = []
    for row in range(height - 1):    # Leave bottom line for status
        cells = []
        for col in range(width):
            real = cx + (col - width  / 2.0) * zoom * aspect / width
            imag = cy + (row - height / 2.0) * zoom / height

            _, smooth = mandelbrot(real, imag, max_iter)
            char      = escape_to_char(smooth, max_iter, palette)
            r, g, b   = escape_to_color(smooth, max_iter, hue_offset)
            cells.append(f'{_color(r, g, b)}{char}')

        rows.append(''.join(cells))

    sys.stdout.write('\x1b[H' + '\n'.join(rows) + RESET)
    sys.stdout.flush()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Mandelbrot set — Unicode density gradient rendering'
    )
    parser.add_argument('--max-iter', type=int, default=80,
                        help='Maximum iterations (higher = more detail, slower)')
    parser.add_argument('--zoom', type=float, default=3.5,
                        help='Initial view width in complex-plane units')
    parser.add_argument('--cx', type=float, default=-0.5,
                        help='Center real coordinate')
    parser.add_argument('--cy', type=float, default=0.0,
                        help='Center imaginary coordinate')
    parser.add_argument('--delay', type=float, default=0.04,
                        help='Seconds between animation frames')
    parser.add_argument('--palette',
                        choices=['unicode', 'classic', 'blocks', 'sparse'],
                        default='unicode',
                        help='Character density palette')
    parser.add_argument('--zoom-to', type=str, default=None,
                        metavar='REAL,IMAG',
                        help='Animate zoom toward this complex coordinate')
    parser.add_argument('--static', action='store_true',
                        help='Render one frame, press Enter to exit')
    args = parser.parse_args()

    palettes = {
        'unicode': PALETTE_UNICODE,
        'classic': PALETTE_CLASSIC,
        'blocks':  PALETTE_BLOCKS,
        'sparse':  PALETTE_SPARSE,
    }
    palette = palettes[args.palette]

    width, height = shutil.get_terminal_size((80, 24))

    # Parse optional zoom target
    zoom_target = None
    if args.zoom_to:
        try:
            tx, ty = map(float, args.zoom_to.split(','))
            zoom_target = (tx, ty)
        except ValueError:
            pass

    cx, cy  = args.cx, args.cy
    zoom    = args.zoom
    hue_off = 0.0

    sys.stdout.write('\x1b[?25l\x1b[2J\x1b[H')
    sys.stdout.flush()

    try:
        while True:
            render_frame(width, height, cx, cy, zoom, args.max_iter, hue_off, palette)

            status = (
                f' Mandelbrot  c = {cx:+.6f} {cy:+.6f}i'
                f'  zoom ×{1.0/zoom:.2e}'
                f'  iter {args.max_iter}'
                f'  palette: {args.palette}'
                f'  ^C to quit'
            )
            sys.stdout.write(f'\x1b[{height};1H\x1b[K{status[:width - 1]}\x1b[0m')
            sys.stdout.flush()

            if args.static:
                input()
                break

            time.sleep(args.delay)

            # Animate: slowly rotate the colour wheel
            hue_off = (hue_off + 0.008) % 1.0

            # If a zoom target is set, drift toward it and zoom in
            if zoom_target:
                tx, ty = zoom_target
                cx   = cx * 0.96 + tx * 0.04
                cy   = cy * 0.96 + ty * 0.04
                zoom = max(zoom * 0.975, 1e-5)

    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write('\x1b[?25h\x1b[0m\n')
        sys.stdout.flush()


if __name__ == '__main__':
    main()
