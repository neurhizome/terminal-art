#!/usr/bin/env python3
# dots_merge_v2.py
# Terminal-width color river with heavy block glyphs, anti-fade HSV merge,
# and a "strange negative" foreground derived from the background.

import argparse
import random
import shutil
import sys
import time
from dataclasses import dataclass
from typing import Tuple, List
import colorsys
import math

# Thick quadrant blocks that interlock nicely and look tetris-adjacent.
GLYPHS = ["██","▓▓","▒▒","░░","░░","▒▒","▓▓","██"]

def clamp8(x: float) -> int:
    x = 0 if x < 0 else (255 if x > 255 else x)
    return int(x)

def rgb_tuple(r: float, g: float, b: float) -> Tuple[int,int,int]:
    return (clamp8(r), clamp8(g), clamp8(b))

def random_color() -> Tuple[int, int, int]:
    return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

@dataclass
class Dot:
    bg: Tuple[int, int, int]
    glyph_idx: int = 0

    def next_glyph_idx(self) -> int:
        return (self.glyph_idx + 1) % len(GLYPHS)

    def fg_from_bg_strange_negative(self, spice: float) -> Tuple[int, int, int]:
        # Convert bg (0..255) -> HSV (0..1)
        r, g, b = [c/255.0 for c in self.bg]
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        # "Strange negative": hue complement + a little orbital drift,
        # invert saturation/value with soft exponents for pop.
        h = (h + 0.5 + random.uniform(-0.06*spice, 0.06*spice)) % 1.0
        s = 1.0 - (s ** 0.65)
        v = 1.0 - (v ** 0.80)
        # Small nudge so we never get dull-black fg
        s = min(1.0, max(0.25, s + 0.10*spice))
        v = min(1.0, max(0.25, v + 0.10*spice))
        rf, gf, bf = colorsys.hsv_to_rgb(h, s, v)
        return rgb_tuple(rf*255, gf*255, bf*255)

    def render(self, fg: Tuple[int,int,int]) -> str:
        fr, fg_, fb = fg
        br, bg_, bb = self.bg
        return f"\x1b[38;2;{fr};{fg_};{fb}m\x1b[48;2;{br};{bg_};{bb}m{GLYPHS[self.glyph_idx]}\x1b[0m"

def dirichlet3():
    a, b, c = random.random(), random.random(), random.random()
    s = a + b + c
    return a/s, b/s, c/s

def hsv_merge_anti_fade(c0: Tuple[int,int,int],
                        c1: Tuple[int,int,int],
                        c2: Tuple[int,int,int],
                        jitter: float,
                        sat_boost: float,
                        val_floor: float) -> Tuple[int,int,int]:
    # Convert to HSV
    def to_hsv(c):
        r, g, b = [x/255.0 for x in c]
        return colorsys.rgb_to_hsv(r, g, b)

    h0, s0, v0 = to_hsv(c0)
    h1, s1, v1 = to_hsv(c1)
    h2, s2, v2 = to_hsv(c2)

    # Unbiased random weights
    w0, w1, w2 = dirichlet3()

    # Circular hue mean via unit vectors
    angs = [2*math.pi*h0, 2*math.pi*h1, 2*math.pi*h2]
    x = w0*math.cos(angs[0]) + w1*math.cos(angs[1]) + w2*math.cos(angs[2])
    y = w0*math.sin(angs[0]) + w1*math.sin(angs[1]) + w2*math.sin(angs[2])
    h = (math.atan2(y, x) / (2*math.pi)) % 1.0

    # Saturation: weighted mean with a gentle boost to resist washout
    s = min(1.0, max(0.0, (w0*s0 + w1*s1 + w2*s2) * sat_boost))

    # Value: lean toward the max so it never dead-fades, then blend in average
    vmax = max(v0, v1, v2)
    vavg = (w0*v0 + w1*v1 + w2*v2)
    v = 0.80*vmax + 0.20*vavg

    # Jitter in HSV space (small)
    h = (h + random.uniform(-0.03*jitter, 0.03*jitter)) % 1.0
    s = min(1.0, max(0.0, s + random.uniform(-0.05*jitter, 0.05*jitter)))
    v = min(1.0, max(val_floor, v + random.uniform(-0.05*jitter, 0.05*jitter)))

    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return rgb_tuple(r*255, g*255, b*255)

def ensure_width(row: List[Dot], width: int) -> List[Dot]:
    n = len(row)
    if width == n:
        return row
    if width < n:
        return row[:width]
    return row + [Dot(random_color(), random.randrange(len(GLYPHS))) for _ in range(width - n)]

def make_initial_row(width: int) -> List[Dot]:
    return [Dot(random_color(), random.randrange(len(GLYPHS))) for _ in range(width)]

def next_row(prev: List[Dot],
             jitter_rgb: int,
             hsv_jitter: float,
             sat_boost: float,
             val_floor: float) -> List[Dot]:
    n = len(prev)
    out: List[Dot] = []
    for i in range(n):
        left = prev[(i - 1) % n]
        selfd = prev[i]
        right = prev[(i + 1) % n]

        # Merge background colors in HSV with anti-fade
        new_bg = hsv_merge_anti_fade(selfd.bg, right.bg, left.bg,
                                     jitter=hsv_jitter,
                                     sat_boost=sat_boost,
                                     val_floor=val_floor)

        # Advance glyph so blocks "spin" and interlock visually
        out.append(Dot(new_bg, selfd.next_glyph_idx()))
    return out

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--rows", type=int, default=0, help="0 = infinite")
    p.add_argument("--delay", type=float, default=0.02, help="Seconds between lines")
    p.add_argument("--seed", type=int, default=None, help="Random seed")
    p.add_argument("--jitter", type=int, default=6, help="Legacy RGB jitter (0..255, mild effect)")
    p.add_argument("--hsv_jitter", type=float, default=1.0, help="HSV jitter multiplier (0..2 is sane)")
    p.add_argument("--sat_boost", type=float, default=1.08, help=">1 resists washout")
    p.add_argument("--val_floor", type=float, default=0.18, help="Keeps value above this")
    args = p.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    # UTF-8 for block glyphs
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    width = max(1, shutil.get_terminal_size(fallback=(80, 24)).columns)
    row = make_initial_row(width)

    line_count = 0
    try:
        while True:
            new_width = max(1, shutil.get_terminal_size(fallback=(80, 24)).columns)
            if new_width != width:
                width = new_width
                row = ensure_width(row, width)

            # Compute per-cell foreground as a "strange negative" of its background
            # right before rendering, so it tracks bg dynamics tightly.
            line_fragments = []
            for dot in row:
                fg = dot.fg_from_bg_strange_negative(spice=0.9)
                line_fragments.append(dot.render(fg))
            sys.stdout.write("".join(line_fragments) + "\n")
            sys.stdout.flush()

            row = next_row(row,
                           jitter_rgb=args.jitter,
                           hsv_jitter=args.hsv_jitter,
                           sat_boost=args.sat_boost,
                           val_floor=args.val_floor)

            line_count += 1
            if args.rows and line_count >= args.rows:
                break
            if args.delay > 0:
                time.sleep(args.delay)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\x1b[0m")
        sys.stdout.flush()

if __name__ == "__main__":
    main()
