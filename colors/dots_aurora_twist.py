#!/usr/bin/env python3
"""
dots_aurora_twist.py — braids-of-gravity, ASCII aurora edition

A twist on the "dots" line pieces: instead of a single evolving strip,
this paints a small terminal "sky" where two drifting gravity wells
interfere to weave luminous braids. It stays dependency‑free, leans on
truecolor ANSI, and tries hard to be gentle on the terminal.

Run it, full‑screen the terminal, and let it breathe. Kill with Ctrl+C.
If your terminal chokes on backgrounds, add --no-bg.
Try changing the seed to get new braids: --seed 13, --seed 42, etc.
"""

import argparse, math, os, random, sys, time
from shutil import get_terminal_size

# --- tiny utils --------------------------------------------------------------

def clamp(x, a, b): 
    return a if x < a else b if x > b else x

def hsv_to_rgb(h, s, v):
    # h in [0,1), s,v in [0,1]
    i = int(h*6.0) % 6
    f = h*6.0 - int(h*6.0)
    p = v*(1.0 - s)
    q = v*(1.0 - f*s)
    t = v*(1.0 - (1.0 - f)*s)
    if i == 0: r,g,b = v,t,p
    elif i == 1: r,g,b = q,v,p
    elif i == 2: r,g,b = p,v,t
    elif i == 3: r,g,b = p,q,v
    elif i == 4: r,g,b = t,p,v
    else:        r,g,b = v,p,q
    return int(r*255), int(g*255), int(b*255)

def fg_rgb(r,g,b): return f"\x1b[38;2;{r};{g};{b}m"
def bg_rgb(r,g,b): return f"\x1b[48;2;{r};{g};{b}m"
RESET = "\x1b[0m"

# Ordered from light to heavy; presets loosely nod to your earlier scripts.
GLYPH_PRESETS = {
    "dots": "·•*✶✷✸✹✺✻✼",
    "braid": " .:/╱╲│─┼╳",
    "blocks": "░▒▓█",
    "contrast": " ▖▗▘▝▚▞▟█",
    "ascii": " .:-=+*#%@",
}

def build_args():
    p = argparse.ArgumentParser(description="Braided gravity aurora in your terminal.")
    p.add_argument("--rows", type=int, default=28, help="rows of sky to render")
    p.add_argument("--fps", type=float, default=22, help="target frames per second")
    p.add_argument("--speed", type=float, default=0.6, help="field drift speed")
    p.add_argument("--scale", type=float, default=0.038, help="distance scale (bigger = looser waves)")
    p.add_argument("--lambda_", type=float, default=0.55, help="spatial wavelength factor")
    p.add_argument("--glyphs", type=str, default="braid", choices=sorted(GLYPH_PRESETS.keys()))
    p.add_argument("--seed", type=int, default=None, help="rng seed for reproducibility")
    p.add_argument("--no-bg", action="store_true", help="disable background color layer")
    p.add_argument("--saturation", type=float, default=0.85, help="color saturation 0..1")
    p.add_argument("--value", type=float, default=0.95, help="color value 0..1")
    return p.parse_args()

# --- field definition --------------------------------------------------------
# Two drifting attractors A and B trace Lissajous‑ish orbits; the field value at
# a cell is the interference of sin(dist(A)) and sin(dist(B)), with a slow
# twist that flips attraction/repulsion—yielding ribbon braids.

def orbit(t, w, h, phase, rx=0.38, ry=0.22):
    cx, cy = w*0.5, h*0.5
    x = cx + math.cos(t + phase*1.7)*w*rx
    y = cy + math.sin(t*0.8 + phase*2.3)*h*ry
    return x, y

def field_value(x, y, t, w, h, lam, scale):
    ax, ay = orbit(t*0.9, w, h, 0.0)
    bx, by = orbit(t*1.1, w, h, 1.3)
    da = math.hypot(x-ax, y-ay)
    db = math.hypot(x-bx, y-by)
    v  = math.sin(da*scale + t*0.9) + math.sin(db*scale*1.1 - t*1.1)
    # Subtle curl so the ribbons feel alive
    curl = math.sin((x*0.013 + y*0.021) + math.sin(t*0.33)*1.7)
    return v + 0.35*curl

# --- renderer ----------------------------------------------------------------

def main():
    args = build_args()
    if args.seed is not None:
        random.seed(args.seed)

    # Terminal geometry
    term_cols = get_terminal_size((120, 40)).columns
    term_lines = get_terminal_size((120, 40)).lines
    cols = max(40, term_cols)
    rows = clamp(args.rows, 8, max(8, term_lines - 2))

    glyphs = GLYPH_PRESETS[args.glyphs]
    G = len(glyphs) - 1
    lam = args.lambda_
    scale = args.scale

    # Precompute normalized coords to keep math cheap
    xs = [i for i in range(cols)]
    ys = [j for j in range(rows)]

    # Hide cursor + set scroll region to our canvas for less flicker
    sys.stdout.write("\x1b[?25l")
    sys.stdout.flush()

    # Double-buffer: remember last frame to avoid repainting identical chars
    last_buf = [""] * rows

    try:
        t0 = time.time()
        frame = 0
        target_dt = 1.0 / max(1e-3, args.fps)

        while True:
            t = (time.time() - t0) * args.speed
            lines = []
            for j in ys:
                y = j + 0.5
                row_chars = []
                for i in xs:
                    x = i + 0.5
                    v = field_value(x, y, t, cols, rows, lam, scale)

                    # Map value to glyph index and hue
                    gidx = int(clamp((v*0.5 + 0.5) * G + 0.5, 0, G))
                    hue  = (0.62 + 0.4*(v*0.5 + 0.5) + (j/rows)*0.12) % 1.0
                    r, g, b = hsv_to_rgb(hue, clamp(args.saturation,0,1), clamp(args.value,0,1))

                    if args.no_bg:
                        cell = f"{fg_rgb(r,g,b)}{glyphs[gidx]}"
                    else:
                        # Complementary background for a soft aurora glow
                        br, bg, bb = hsv_to_rgb((hue+0.5)%1.0, clamp(args.saturation*0.55,0,1), 0.18 + 0.18*(gidx/G if G>0 else 0))
                        cell = f"{bg_rgb(br,bg,bb)}{fg_rgb(r,g,b)}{glyphs[gidx]}"
                    row_chars.append(cell)
                line = "".join(row_chars) + RESET
                lines.append(line)

            # Compose full frame
            frame_str = "\n".join(lines)

            # If previous line same, skip to reduce flicker; otherwise paint full row
            # (Simple heuristic: check whole frame every N frames to resync.)
            if frame % 200 == 0 or any(lines[j] != last_buf[j] for j in range(rows)):
                sys.stdout.write("\x1b[H")  # home
                sys.stdout.write(frame_str)
                sys.stdout.flush()
                last_buf = lines

            frame += 1
            # Frame pacing
            dt = target_dt - (time.time() - (t0 + frame/args.fps/args.speed))
            if dt > 0:
                time.sleep(min(dt, 0.02))

    except KeyboardInterrupt:
        pass
    finally:
        # Reset terminal state
        sys.stdout.write(RESET + "\x1b[?25h\n")
        sys.stdout.flush()

if __name__ == "__main__":
    main()
