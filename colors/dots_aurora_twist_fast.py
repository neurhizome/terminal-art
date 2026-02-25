#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dots_aurora_twist_fast.py — resize‑aware aurora braids with smooth animation

Why this runs smoother:
• Handles live terminal resizing (SIGWINCH) and auto-fits to the full screen.
• Higher default FPS with proper frame pacing (monotonic clock).
• CPU-friendly math: sine lookup table + hue palette cache.
• Dirty-row redraw: only repaint rows that changed.
• Optional sampling stride to trade detail for speed (e.g., --stride 2).
• Optional alternate screen buffer for flicker-free full-screen display.

Controls:
  --fps 55            target frames per second
  --stride 1          1 = full resolution, 2 or 3 = faster
  --speed 0.8         field drift speed (lower = gentler, higher = wavier)
  --glyphs ascii      choose from presets or pass --glyphs-custom "..."
  --no-bg             disable aurora background glow
  --no-alt            don't use the terminal's alternate screen
  --seed N            set RNG for reproducible drift nuances

Exit with Ctrl+C.
"""

import argparse, math, os, random, signal, sys, time
from shutil import get_terminal_size

# ------------------------- small utils ---------------------------------------

RESET = "\x1b[0m"
HIDE  = "\x1b[?25l"
SHOW  = "\x1b[?25h"
ALT_ON  = "\x1b[?1049h"
ALT_OFF = "\x1b[?1049l"

def clamp(x, a, b):
    return a if x < a else b if x > b else x

def hsv_to_rgb(h, s, v):
    i = int(h*6.0) % 6
    f = h*6.0 - int(h*6.0)
    p = v*(1.0 - s)
    q = v*(1.0 - f*s)
    t = v*(1.0 - (1.0 - f)*s)
    if   i == 0: r,g,b = v,t,p
    elif i == 1: r,g,b = q,v,p
    elif i == 2: r,g,b = p,v,t
    elif i == 3: r,g,b = p,q,v
    elif i == 4: r,g,b = t,p,v
    else:        r,g,b = v,p,q
    return int(r*255), int(g*255), int(b*255)

def fg_rgb(r,g,b): return f"\x1b[38;2;{r};{g};{b}m"
def bg_rgb(r,g,b): return f"\x1b[48;2;{r};{g};{b}m"

GLYPH_PRESETS = {
    "dots":     "·•*✶✷✸✹✺✻✼",
    "braid":    " .:/╱╲│─┼╳",
    "blocks":   "░▒▓█",
    "contrast": " ▖▗▘▝▚▞▟█",
    "ascii":    " .:-=+*#%@",
}

# ------------------------ fast trig & palettes -------------------------------

LUT_SIZE = 8192
TAU = math.tau if hasattr(math, "tau") else 2*math.pi
_sin_lut = [math.sin(TAU * i / LUT_SIZE) for i in range(LUT_SIZE)]

def fast_sin(x):
    y = x % TAU
    return _sin_lut[int(y * (LUT_SIZE/TAU)) & (LUT_SIZE-1)]

class HueCache:
    """Quantize hue to 720 steps for cheap color codes."""
    def __init__(self, s=0.9, v=0.95, bg_scale=0.55):
        self.s, self.v = clamp(s,0,1), clamp(v,0,1)
        self.bg_scale = bg_scale
        self.steps = 720
        self.fg = [None]*self.steps
        self.bg = [None]*self.steps

    def get_codes(self, h, use_bg, g_norm):
        idx = int((h % 1.0) * self.steps) % self.steps
        if self.fg[idx] is None:
            r,g,b = hsv_to_rgb(idx/self.steps, self.s, self.v)
            self.fg[idx] = fg_rgb(r,g,b)
            br,bg,bb = hsv_to_rgb(((idx/self.steps)+0.5)%1.0, self.s*self.bg_scale, 0.18 + 0.18*g_norm)
            self.bg[idx] = bg_rgb(br,bg,bb)
        if use_bg:
            return self.bg[idx], self.fg[idx]
        else:
            return "", self.fg[idx]

# --------------------------- core field --------------------------------------

def orbit(t, w, h, phase, rx=0.38, ry=0.22):
    cx, cy = w*0.5, h*0.5
    x = cx + math.cos(t + phase*1.7)*w*rx
    y = cy + math.sin(t*0.8 + phase*2.3)*h*ry
    return x, y

def field_value(x, y, t, w, h, scale):
    ax, ay = orbit(t*0.9, w, h, 0.0)
    bx, by = orbit(t*1.1, w, h, 1.3)
    da = math.hypot(x-ax, y-ay)
    db = math.hypot(x-bx, y-by)
    v  = fast_sin(da*scale + t*0.9) + fast_sin(db*scale*1.1 - t*1.1)
    curl = fast_sin((x*0.013 + y*0.021) + fast_sin(t*0.33)*1.7)
    return v + 0.35*curl

# ------------------------ render / resize loop -------------------------------

_resized = True
def _mark_resized(signum=None, frame=None):
    global _resized
    _resized = True

def get_dims(rows_hint=None):
    ts = get_terminal_size((120, 40))
    cols = max(40, ts.columns)
    # Leave one line for a comfy bottom margin
    rows = max(8, ts.lines - 1) if rows_hint is None else rows_hint
    return cols, rows

def build_args():
    ap = argparse.ArgumentParser(description="Resize-aware aurora braids.")
    ap.add_argument("--fps", type=float, default=55.0)
    ap.add_argument("--speed", type=float, default=0.8)
    ap.add_argument("--scale", type=float, default=0.035, help="distance scale")
    ap.add_argument("--saturation", type=float, default=0.88)
    ap.add_argument("--value", type=float, default=0.96)
    ap.add_argument("--glyphs", type=str, default="ascii", choices=sorted(GLYPH_PRESETS.keys()))
    ap.add_argument("--glyphs-custom", type=str, default=None, help="override with your glyph string")
    ap.add_argument("--stride", type=int, default=1, help="sample every N cols/rows for speed")
    ap.add_argument("--no-bg", action="store_true")
    ap.add_argument("--no-alt", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    return ap.parse_args()

def main():
    global _resized
    args = build_args()
    if args.seed is not None:
        random.seed(args.seed)

    glyphs = (args.glyphs_custom if args.glyphs_custom else GLYPH_PRESETS[args.glyphs])
    G = max(1, len(glyphs) - 1)

    # install resize handler
    try:
        signal.signal(signal.SIGWINCH, _mark_resized)
    except Exception:
        pass  # non-POSIX envs may not have it

    hue_cache = HueCache(args.saturation, args.value, bg_scale=0.55)
    use_bg = (not args.no_bg)

    if not args.no_alt:
        sys.stdout.write(ALT_ON)
    sys.stdout.write(HIDE)
    sys.stdout.flush()

    cols, rows = get_dims()
    last_rows = [""] * rows  # per-row dirty tracking

    # Useful for stride sampling
    stride = max(1, int(args.stride))

    # frame timing
    target_dt = 1.0 / max(1e-3, args.fps)
    t = 0.0
    last = time.perf_counter()

    try:
        # clear screen & home at start
        sys.stdout.write("\x1b[2J\x1b[H")
        sys.stdout.flush()

        while True:
            now = time.perf_counter()
            dt = now - last
            last = now
            t += dt * args.speed

            if _resized:
                _resized = False
                cols, rows = get_dims()
                last_rows = [""] * rows
                # full clear on resize
                sys.stdout.write("\x1b[2J\x1b[H")
                sys.stdout.flush()

            w = cols
            h = rows
            # Build this frame into a list of strings (one per row), sampling by stride
            new_rows = [None] * rows
            for j in range(0, rows, 1):
                # compute y once; slight subcell shift to avoid checkerboarding
                y = (j + 0.37) * 1.0
                row_chars = []
                i = 0
                while i < cols:
                    x = (i + 0.53) * 1.0
                    v = field_value(x, y, t, w, h, args.scale)

                    gidx = int(clamp((v*0.5 + 0.5) * G + 0.5, 0, G))
                    g_norm = (gidx / G) if G > 0 else 0.0
                    hue  = (0.62 + 0.40*(v*0.5 + 0.5) + (j/rows)*0.12) % 1.0

                    bgc, fgc = hue_cache.get_codes(hue, use_bg, g_norm)
                    cell = f"{bgc}{fgc}{glyphs[gidx]}"
                    row_chars.append(cell)

                    # Fill skipped columns with same cell to keep aspect
                    if stride > 1:
                        span = min(stride-1, cols - (i+1))
                        if span > 0:
                            row_chars.append(cell * span)
                    i += stride

                line = "".join(row_chars) + RESET
                new_rows[j] = line

            # Only repaint rows that changed.
            # Move cursor only when needed; \x1b[{row};1H positions to row 1-based.
            for j in range(rows):
                if new_rows[j] != (last_rows[j] if j < len(last_rows) else ""):
                    sys.stdout.write(f"\x1b[{j+1};1H")
                    sys.stdout.write(new_rows[j])

            sys.stdout.flush()
            last_rows = new_rows

            # Frame pacing
            sleep_for = target_dt - (time.perf_counter() - now)
            if sleep_for > 0:
                # Cap short sleeps, avoid oversleeping
                time.sleep(min(sleep_for, 0.010))

    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write(RESET + SHOW)
        if not args.no_alt:
            sys.stdout.write(ALT_OFF)
        sys.stdout.flush()

if __name__ == "__main__":
    main()
