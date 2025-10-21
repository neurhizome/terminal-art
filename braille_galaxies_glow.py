#!/usr/bin/env python3
# braille_galaxies_glow.py
#
# Braille galaxies with diffusing color glow.
# - Stars deposit energy into a high-res microgrid (2x4 subpixels per braille cell).
# - A persistent "glow" field (per braille cell) stores color brightness that decays
#   and DIFFUSES across the background, so empty space slowly fills with blended hues.
# - Optional FG/BG color (anti-colors for legibility), with BG driven by the glow.
#
# Run examples:
#   python3 braille_galaxies_glow.py --color
#   python3 braille_galaxies_glow.py --color --galaxies 3 --stars 1500 --delay 0.015
#   python3 braille_galaxies_glow.py --color --gain 0.16 --decay 0.92 --swirl 2.6 --radial 0.7
#   python3 braille_galaxies_glow.py --color --glow_gain 0.12 --glow_diffuse 0.35 --glow_decay 0.985
#
# Ctrl-C to exit.

import argparse, random, shutil, sys, time, math, colorsys
from dataclasses import dataclass
from typing import List, Tuple

# ---------- Braille helpers ----------
# Dot numbering:
# left column: 1,2,3,7 → bit indices 0,1,2,6
# right column: 4,5,6,8 → bit indices 3,4,5,7
DOT_INDEX = (
    (0, 3),  # y=0
    (1, 4),  # y=1
    (2, 5),  # y=2
    (6, 7),  # y=3
)

def braille_char(mask: int) -> str:
    return chr(0x2800 + (mask & 0xFF))

# ---------- Color helpers ----------
def clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)

def hsv_to_rgb8(h: float, s: float, v: float) -> Tuple[int,int,int]:
    r,g,b = colorsys.hsv_to_rgb(h%1.0, clamp01(s), clamp01(v))
    return int(r*255), int(g*255), int(b*255)

def anti_fg_bg(h: float, s: float, v: float) -> Tuple[Tuple[int,int,int], Tuple[int,int,int]]:
    """Complementary anti-colors; FG gets v, BG gets inverted brightness."""
    fg = hsv_to_rgb8(h, 0.35 + 0.65*s, v)
    hb = (h + 0.5) % 1.0
    sb = clamp01(0.45 + 0.55*(1.0 - s))
    vb = clamp01(0.85 - 0.60*v)
    bg = hsv_to_rgb8(hb, sb, vb)
    return fg, bg

def bg_from_glow(h: float, glow_v: float) -> Tuple[int,int,int]:
    """Map glow brightness to a background color using hue h and a soft palette."""
    v = clamp01(0.08 + glow_v)     # floor so it never goes pitch black
    s = clamp01(0.35 + 0.45*min(1.0, glow_v*1.2))
    return hsv_to_rgb8(h, s, v)

# ---------- Galaxy dynamics ----------
@dataclass
class Star:
    x: float
    y: float
    vx: float
    vy: float
    g: int   # galaxy id

def make_stars(count: int, centers: List[Tuple[float,float]], box_w: int, box_h: int,
               spread: float, jitter: float) -> List[Star]:
    out = []
    for i in range(count):
        gi = i % len(centers)
        cx, cy = centers[gi]
        # Gaussian-ish spawn around the center
        r = abs(random.gauss(0, spread))
        theta = random.random() * 2*math.pi
        x = cx + r*math.cos(theta) + random.uniform(-jitter, jitter)
        y = cy + r*math.sin(theta) + random.uniform(-jitter, jitter)
        x = x % box_w; y = y % box_h
        out.append(Star(x, y, 0.0, 0.0, gi))
    return out

def spiral_velocity(x: float, y: float, cx: float, cy: float,
                    swirl: float, radial: float, arms: int, t: float) -> Tuple[float,float]:
    # Polar coords around center
    dx, dy = x - cx, y - cy
    r = math.hypot(dx, dy) + 1e-6
    ang = math.atan2(dy, dx)
    # Tangential swirl (perpendicular to radius)
    vt = swirl / (0.5 + 0.02*r)  # slower at the edge
    tx, ty = -dy / r * vt, dx / r * vt
    # Arm modulation: push outward along k-armed spiral ridges
    arm = math.cos(arms*ang - 0.6*t)  # drifting phase gives rotation
    vr = radial * (0.25 + 0.75*(arm*0.5+0.5)) / (1.0 + 0.002*r)
    rx, ry = (dx / r) * vr, (dy / r) * vr
    return tx + rx, ty + ry

# ---------- Renderer ----------
def render_frame(micro, cols, rows, gain, hue_field, glow_v, use_color: bool, bg_mode: str) -> str:
    """Convert 2x4 microgrid into Braille chars line by line.
       bg_mode: 'glow' uses diffusing background, 'anti' uses complementary anti-color."""
    lines = []
    for cy in range(rows):
        y0 = cy*4
        parts = []
        for cx in range(cols):
            x0 = cx*2
            vals = [
                micro[y0+0][x0+0], micro[y0+0][x0+1],
                micro[y0+1][x0+0], micro[y0+1][x0+1],
                micro[y0+2][x0+0], micro[y0+2][x0+1],
                micro[y0+3][x0+0], micro[y0+3][x0+1],
            ]
            s = sum(vals)
            n_on = int(s * gain)
            # Hue from field
            h = hue_field[cy][cx]
            # Background from glow (always; gives colored empty space)
            bg = bg_from_glow(h, glow_v[cy][cx])
            if n_on <= 0:
                # Just draw background color; character can be space
                if use_color:
                    parts.append(f"\x1b[48;2;{bg[0]};{bg[1]};{bg[2]}m \x1b[0m")
                else:
                    parts.append(" ")
            else:
                # Light top-n subpixels into a braille mask
                order = sorted(range(8), key=lambda k: vals[k], reverse=True)
                mask = 0
                for k in order[: min(8, n_on)]:
                    sy = k//2; sx = k%2
                    bit = DOT_INDEX[sy][sx]
                    mask |= (1 << bit)
                ch = braille_char(mask)
                if use_color:
                    # Foreground brightness scales with local intensity; keep it punchy
                    v = max(0.15, min(1.0, 0.20 + 0.12*s + 0.06*n_on))
                    s_col = max(0.35, min(1.0, 0.45 + 0.10*n_on))
                    if bg_mode == "anti":
                        fg, bgc = anti_fg_bg(h, s_col, v)
                        parts.append(f"\x1b[38;2;{fg[0]};{fg[1]};{fg[2]}m\x1b[48;2;{bgc[0]};{bgc[1]};{bgc[2]}m{ch}\x1b[0m")
                    else:
                        fg = hsv_to_rgb8(h, s_col, v)
                        parts.append(f"\x1b[38;2;{fg[0]};{fg[1]};{fg[2]}m\x1b[48;2;{bg[0]};{bg[1]};{bg[2]}m{ch}\x1b[0m")
                else:
                    parts.append(ch)
        lines.append("".join(parts))
    return "\n".join(lines)

def main():
    ap = argparse.ArgumentParser(description="Braille galaxies — with diffusing background glow")
    ap.add_argument("--rows", type=int, default=0, help="frames to render (0 = infinite)")
    ap.add_argument("--delay", type=float, default=0.02, help="seconds between frames")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--galaxies", type=int, default=2)
    ap.add_argument("--stars", type=int, default=1200)
    ap.add_argument("--spread", type=float, default=28.0, help="spawn stddev (pixels) around centers")
    ap.add_argument("--jitter", type=float, default=2.0, help="spawn jitter")
    ap.add_argument("--swirl", type=float, default=2.2, help="tangential swirl strength")
    ap.add_argument("--radial", type=float, default=0.55, help="radial push along arms")
    ap.add_argument("--arms", type=int, default=2, help="number of spiral arms per galaxy")
    ap.add_argument("--gain", type=float, default=0.14, help="dots lit per cell per unit energy")
    ap.add_argument("--decay", type=float, default=0.93, help="trail decay per frame (microgrid)")
    ap.add_argument("--diffuse", type=float, default=0.0, help="optional micro blur 0..1 (costly if >0)")
    ap.add_argument("--color", action="store_true", help="enable color FG/BG")
    # Glow field controls
    ap.add_argument("--glow_gain", type=float, default=0.10, help="deposit gain from energy into background glow")
    ap.add_argument("--glow_decay", type=float, default=0.990, help="background glow decay per frame (close to 1 = persistent)")
    ap.add_argument("--glow_diffuse", type=float, default=0.25, help="diffusion rate of glow across the background (0..1)")
    ap.add_argument("--bg_mode", default="glow", choices=["glow","anti"], help="use diffusing glow or anti-color backgrounds")
    args = ap.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    # Prepare terminal and canvas size
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    cols, lines = shutil.get_terminal_size(fallback=(100, 30))
    rows_cells = max(6, lines - 2)
    cols_cells = max(40, cols)
    micro_w = cols_cells * 2
    micro_h = rows_cells * 4

    # Galaxy centers arranged on a ring
    centers: List[Tuple[float,float]] = []
    r_ring = min(micro_w, micro_h) * 0.20
    cx0, cy0 = micro_w * 0.5, micro_h * 0.5
    for gi in range(max(1, args.galaxies)):
        a = 2*math.pi * gi / max(1, args.galaxies)
        centers.append((cx0 + r_ring*math.cos(a), cy0 + r_ring*math.sin(a)))

    # Star swarm
    stars = make_stars(args.stars, centers, micro_w, micro_h, args.spread, args.jitter)

    # High-res microgrid (float brightness)
    micro = [[0.0 for _ in range(micro_w)] for _ in range(micro_h)]
    # Hue field per Braille cell (for color)
    hue_field = [[random.random() for _ in range(cols_cells)] for _ in range(rows_cells)]
    # Persistent glow brightness per Braille cell
    glow_v = [[0.0 for _ in range(cols_cells)] for _ in range(rows_cells)]

    # In-place animation setup
    hide_cursor = "\x1b[?25l"
    show_cursor = "\x1b[?25h"
    clear = "\x1b[2J"
    home = "\x1b[H"
    sys.stdout.write(hide_cursor + clear)
    sys.stdout.flush()

    t = 0.0
    frame = 0
    try:
        while True:
            # Optional micro diffusion (cheap box blur)
            if args.diffuse > 0.0 and (frame % 2 == 0):
                w = micro_w; h = micro_h
                alpha = max(0.0, min(1.0, args.diffuse)) * 0.25
                for y in range(1, h-1):
                    row = micro[y]
                    up = micro[y-1]; dn = micro[y+1]
                    for x in range(1, w-1):
                        nsum = up[x] + dn[x] + row[x-1] + row[x+1]
                        row[x] = (1.0 - alpha) * row[x] + alpha * (nsum * 0.25)

            # Decay trails in microgrid
            for y in range(micro_h):
                row = micro[y]
                for x in range(micro_w):
                    row[x] *= args.decay

            # Move & deposit stars
            for s in stars:
                cx, cy = centers[s.g]
                vx, vy = spiral_velocity(s.x, s.y, cx, cy, args.swirl, args.radial, args.arms, t)
                vx += random.uniform(-0.05, 0.05)
                vy += random.uniform(-0.05, 0.05)
                s.vx = 0.85*s.vx + 0.15*vx
                s.vy = 0.85*s.vy + 0.15*vy
                s.x = (s.x + s.vx) % micro_w
                s.y = (s.y + s.vy) % micro_h

                # Bilinear splat
                ix = int(s.x); iy = int(s.y)
                fx = s.x - ix; fy = s.y - iy
                x1 = (ix + 1) % micro_w; y1 = (iy + 1) % micro_h
                w00 = (1-fx)*(1-fy); w10 = fx*(1-fy); w01 = (1-fx)*fy; w11 = fx*fy
                e = 1.7
                micro[iy][ix]       += e * w00
                micro[iy][x1]       += e * w10
                micro[y1][ix]       += e * w01
                micro[y1][x1]       += e * w11

            # Hue drift tied to centers (soft, for color)
            if args.color:
                for ry in range(rows_cells):
                    for rx in range(cols_cells):
                        x = rx*2 + 1; y = ry*4 + 2
                        # angle to nearest center
                        best = None; bh = 0.0
                        for (gx, gy) in centers:
                            dx, dy = x - gx, y - gy
                            d2 = dx*dx + dy*dy
                            if best is None or d2 < best:
                                best = d2
                                bh = (math.atan2(dy, dx)/(2*math.pi)) % 1.0
                        hue_field[ry][rx] = (0.985*hue_field[ry][rx] + 0.015*bh + 0.001*math.sin(0.25*t)) % 1.0

            # Downsample micro to per-cell sums and update glow
            # We also diffuse glow outward so background slowly fills with color.
            for ry in range(rows_cells):
                y0 = ry*4
                row_glow = glow_v[ry]
                for rx in range(cols_cells):
                    x0 = rx*2
                    s = (micro[y0+0][x0+0] + micro[y0+0][x0+1] +
                         micro[y0+1][x0+0] + micro[y0+1][x0+1] +
                         micro[y0+2][x0+0] + micro[y0+2][x0+1] +
                         micro[y0+3][x0+0] + micro[y0+3][x0+1])
                    # Deposit into glow brightness (decay applied globally below)
                    row_glow[rx] += args.glow_gain * s

            # Glow decay
            gdec = max(0.0, min(1.0, args.glow_decay))
            for ry in range(rows_cells):
                for rx in range(cols_cells):
                    glow_v[ry][rx] *= gdec

            # Glow diffusion (toroidal wrap so color reaches edges and blends across)
            alpha = max(0.0, min(1.0, args.glow_diffuse)) * 0.25
            if alpha > 0.0:
                new_glow = [[0.0 for _ in range(cols_cells)] for _ in range(rows_cells)]
                for ry in range(rows_cells):
                    up = (ry - 1) % rows_cells
                    dn = (ry + 1) % rows_cells
                    for rx in range(cols_cells):
                        lt = (rx - 1) % cols_cells
                        rt = (rx + 1) % cols_cells
                        center = glow_v[ry][rx]
                        nb = glow_v[ry][lt] + glow_v[ry][rt] + glow_v[up][rx] + glow_v[dn][rx]
                        new_glow[ry][rx] = (1.0 - alpha) * center + alpha * (0.25 * nb)
                glow_v = new_glow

            # Compose and draw
            frame_text = render_frame(micro, cols_cells, rows_cells, gain=args.gain,
                                      hue_field=hue_field, glow_v=glow_v,
                                      use_color=args.color, bg_mode=args.bg_mode)
            sys.stdout.write(home + frame_text + "\n")
            sys.stdout.flush()

            frame += 1
            t += 1.0
            if args.rows and frame >= args.rows:
                break
            if args.delay > 0:
                time.sleep(args.delay)

            # Handle resize
            new_cols, new_lines = shutil.get_terminal_size(fallback=(cols, lines))
            if new_cols != cols or new_lines != lines:
                cols, lines = new_cols, new_lines
                rows_cells = max(6, lines - 2)
                cols_cells = max(40, cols)
                micro_w = cols_cells * 2
                micro_h = rows_cells * 4
                # Reallocate fields
                micro = [[0.0 for _ in range(micro_w)] for _ in range(micro_h)]
                hue_field = [[random.random() for _ in range(cols_cells)] for _ in range(rows_cells)]
                glow_v = [[0.0 for _ in range(cols_cells)] for _ in range(rows_cells)]
                # Re-center galaxies & re-spawn stars
                centers.clear()
                r_ring = min(micro_w, micro_h) * 0.20
                cx0, cy0 = micro_w * 0.5, micro_h * 0.5
                for gi in range(max(1, args.galaxies)):
                    a = 2*math.pi * gi / max(1, args.galaxies)
                    centers.append((cx0 + r_ring*math.cos(a), cy0 + r_ring*math.sin(a)))
                stars = make_stars(args.stars, centers, micro_w, micro_h, args.spread, args.jitter)

    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\x1b[0m" + show_cursor + "\n")
        sys.stdout.flush()

if __name__ == "__main__":
    main()
