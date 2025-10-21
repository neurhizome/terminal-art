#!/usr/bin/env python3
# braille_dots_collide.py (patched)
#
# Braille-dot physics engine: star swarms with short-range repulsion,
# black holes (event horizons), and supernovas (radial blasts).
# Truecolor optional, but monochrome looks great. Stdlib-only.
#
# Changes in this patch:
# - Robust wrapping: wrap() now uses modulo so values always land in [0,m).
# - Safe deposit: ix/iy are wrapped with % to prevent occasional out-of-range.
# - Optional speed clamp to avoid huge leaps during intense novae.
#
# Run examples:
#   python3 braille_dots_collide.py
#   python3 braille_dots_collide.py --color --blackholes 2 --supernova_rate 0.02 --delay 0.012

import argparse, random, shutil, sys, time, math, colorsys
from dataclasses import dataclass
from typing import List, Tuple, DefaultDict
from collections import defaultdict

# --------- Braille helpers ---------
DOT_INDEX = (
    (0, 3),  # row 0
    (1, 4),  # row 1
    (2, 5),  # row 2
    (6, 7),  # row 3
)
def braille_char(mask: int) -> str:
    return chr(0x2800 + (mask & 0xFF))

def clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)

def hsv_to_rgb8(h: float, s: float, v: float) -> Tuple[int,int,int]:
    r,g,b = colorsys.hsv_to_rgb(h%1.0, clamp01(s), clamp01(v))
    return int(r*255), int(g*255), int(b*255)

def anti_fg_bg(h: float, s: float, v: float) -> Tuple[Tuple[int,int,int], Tuple[int,int,int]]:
    fg = hsv_to_rgb8(h, 0.35 + 0.65*s, v)
    hb = (h + 0.5) % 1.0
    sb = clamp01(0.45 + 0.55*(1.0 - s))
    vb = clamp01(0.85 - 0.60*v)
    bg = hsv_to_rgb8(hb, sb, vb)
    return fg, bg

# --------- Entities ---------
@dataclass
class Star:
    x: float; y: float
    vx: float; vy: float
    hue: float

@dataclass
class BlackHole:
    x: float; y: float
    mass: float
    event_r: float   # capture radius in micro-pixels

@dataclass
class Supernova:
    x: float; y: float
    strength: float
    radius: float
    ttl: int

# --------- Spatial hashing for neighbor repulsion ---------
class HashGrid:
    def __init__(self, w: int, h: int, cell: float):
        self.w = w; self.h = h; self.cell = max(2.0, cell)
        self.grid: DefaultDict[Tuple[int,int], List[int]] = defaultdict(list)
    def _k(self, x: float, y: float) -> Tuple[int,int]:
        return int(x//self.cell), int(y//self.cell)
    def rebuild(self, stars: List[Star]):
        self.grid.clear()
        for i, s in enumerate(stars):
            self.grid[self._k(s.x, s.y)].append(i)
    def neighbors(self, x: float, y: float):
        cx, cy = self._k(x, y)
        for dy in (-1,0,1):
            for dx in (-1,0,1):
                yield from self.grid.get((cx+dx, cy+dy), [])

# --------- Physics ---------
def wrap(x: float, m: int) -> float:
    if m <= 0: return x
    # Proper modulo wrapping keeps values in [0, m)
    return x % m

def step(stars: List[Star], holes: List[BlackHole], novas: List[Supernova],
         micro_w: int, micro_h: int, grid: HashGrid,
         repel: float, repel_r: float, friction: float,
         bh_grav: float, soft: float, dt: float, vmax: float = 5.0):
    grid.rebuild(stars)
    r2_soft = soft*soft
    repel_r2 = repel_r*repel_r
    for i, s in enumerate(stars):
        ax = ay = 0.0
        # Repulsion
        for j in grid.neighbors(s.x, s.y):
            if j == i: continue
            t = stars[j]
            dx = s.x - t.x; dy = s.y - t.y
            if dx >  micro_w*0.5: dx -= micro_w
            if dx < -micro_w*0.5: dx += micro_w
            if dy >  micro_h*0.5: dy -= micro_h
            if dy < -micro_h*0.5: dy += micro_h
            d2 = dx*dx + dy*dy
            if d2 < 1e-6 or d2 > repel_r2: continue
            inv = 1.0 / math.sqrt(d2 + 1e-9)
            f = repel * (1.0 / (d2 + 1e-6))
            ax += dx * f * inv; ay += dy * f * inv

        # Black hole gravity & capture
        for bh in holes:
            dx = bh.x - s.x; dy = bh.y - s.y
            if dx >  micro_w*0.5: dx -= micro_w
            if dx < -micro_w*0.5: dx += micro_w
            if dy >  micro_h*0.5: dy -= micro_h
            if dy < -micro_h*0.5: dy += micro_h
            d2 = dx*dx + dy*dy + r2_soft
            invr3 = 1.0 / (d2*math.sqrt(d2))
            f = bh_grav * bh.mass * invr3
            ax += dx * f; ay += dy * f
            if d2 < (bh.event_r*bh.event_r):
                # respawn far away
                s.x = random.random()*micro_w; s.y = random.random()*micro_h
                s.vx = random.uniform(-1.0,1.0); s.vy = random.uniform(-1.0,1.0)
                s.hue = random.random()
                novas.append(Supernova(bh.x, bh.y, strength=1200.0, radius=bh.event_r*2.4, ttl=18))

        # Supernova pushes
        for nv in list(novas):
            dx = s.x - nv.x; dy = s.y - nv.y
            if dx >  micro_w*0.5: dx -= micro_w
            if dx < -micro_w*0.5: dx += micro_w
            if dy >  micro_h*0.5: dy -= micro_h
            if dy < -micro_h*0.5: dy += micro_h
            d2 = dx*dx + dy*dy
            if d2 < (nv.radius*nv.radius):
                r = math.sqrt(d2) + 1e-6
                fall = math.exp(-0.5*(r/nv.radius)**2)
                ax += (dx/r) * nv.strength * fall
                ay += (dy/r) * nv.strength * fall

        # Integrate with friction and clamp speed
        s.vx = (s.vx + ax*dt) * friction
        s.vy = (s.vy + ay*dt) * friction
        spd2 = s.vx*s.vx + s.vy*s.vy
        if spd2 > vmax*vmax:
            k = vmax / math.sqrt(spd2 + 1e-12)
            s.vx *= k; s.vy *= k

        s.x = wrap(s.x + s.vx*dt, micro_w)
        s.y = wrap(s.y + s.vy*dt, micro_h)

    # Age novae
    for i in range(len(novas)-1, -1, -1):
        novas[i].ttl -= 1
        if novas[i].ttl <= 0:
            novas.pop(i)

# --------- Rendering ---------
def render_frame(micro, cols, rows, gain, gamma, color=False, hue_field=None, bg=None) -> str:
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
            s = sum(v**gamma for v in vals)
            n_on = int(s * gain)
            if n_on <= 0:
                if color and bg is not None:
                    parts.append(f"\x1b[48;2;{bg[0]};{bg[1]};{bg[2]}m \x1b[0m")
                else:
                    parts.append(" ")
                continue
            order = sorted(range(8), key=lambda k: vals[k], reverse=True)
            mask = 0
            for k in order[: min(8, n_on)]:
                sy = k//2; sx = k%2
                bit = DOT_INDEX[sy][sx]
                mask |= (1 << bit)
            ch = chr(0x2800 + mask)
            if color and hue_field is not None:
                h = hue_field[cy][cx]
                v = clamp01(0.18 + 0.08*s + 0.05*n_on)
                s_col = clamp01(0.45 + 0.10*n_on)
                fg, bgc = anti_fg_bg(h, s_col, v)
                parts.append(f"\x1b[38;2;{fg[0]};{fg[1]};{fg[2]}m\x1b[48;2;{bgc[0]};{bgc[1]};{bgc[2]}m{ch}\x1b[0m")
            else:
                parts.append(ch)
        lines.append("".join(parts))
    return "\n".join(lines)

def main():
    ap = argparse.ArgumentParser(description="Braille dots: collisions + black holes + supernovas")
    ap.add_argument("--rows", type=int, default=0, help="frames to render (0 = infinite)")
    ap.add_argument("--delay", type=float, default=0.02, help="seconds per frame")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--stars", type=int, default=1000)
    ap.add_argument("--repel", type=float, default=80.0, help="repulsion strength")
    ap.add_argument("--repel_r", type=float, default=9.0, help="repulsion radius (micro px)")
    ap.add_argument("--friction", type=float, default=0.995, help="velocity damping per step")
    ap.add_argument("--blackholes", type=int, default=1)
    ap.add_argument("--bh_grav", type=float, default=1200.0, help="BH gravity constant")
    ap.add_argument("--bh_mass", type=float, default=1.0)
    ap.add_argument("--bh_event", type=float, default=14.0, help="event horizon radius (micro px)")
    ap.add_argument("--supernova_rate", type=float, default=0.01, help="probability per frame to spawn a nova")
    ap.add_argument("--nova_strength", type=float, default=1500.0)
    ap.add_argument("--nova_radius", type=float, default=28.0)
    ap.add_argument("--nova_ttl", type=int, default=22)
    ap.add_argument("--gain", type=float, default=0.16, help="dots lit per cell per unit energy")
    ap.add_argument("--gamma", type=float, default=0.8, help="intensity gamma (<1 brighter)")
    ap.add_argument("--micro_blur", type=float, default=0.20, help="trail blur 0..1")
    ap.add_argument("--decay", type=float, default=0.92, help="trail decay per frame")
    ap.add_argument("--color", action="store_true", help="enable color anti-FG/BG")
    args = ap.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    term_cols, term_lines = shutil.get_terminal_size(fallback=(100, 30))
    rows = max(6, term_lines - 2)
    cols = max(60, term_cols)
    micro_w = cols * 2
    micro_h = rows * 4

    # init stars
    stars: List[Star] = []
    for _ in range(args.stars):
        x = random.random()*micro_w; y = random.random()*micro_h
        ang = random.random()*2*math.pi
        spd = random.uniform(0.0, 1.0)
        vx = math.cos(ang)*spd; vy = math.sin(ang)*spd
        stars.append(Star(x,y,vx,vy, random.random()))

    # black holes on a ring
    holes: List[BlackHole] = []
    for i in range(max(1, args.blackholes)):
        a = 2*math.pi * i / max(1, args.blackholes)
        r = min(micro_w, micro_h)*0.20
        cx = micro_w*0.5 + r*math.cos(a)
        cy = micro_h*0.5 + r*math.sin(a)
        holes.append(BlackHole(cx, cy, mass=args.bh_mass, event_r=args.bh_event))

    novas: List[Supernova] = []

    micro = [[0.0 for _ in range(micro_w)] for _ in range(micro_h)]
    hue_field = [[random.random() for _ in range(cols)] for _ in range(rows)]

    grid = HashGrid(micro_w, micro_h, cell=max(4.0, args.repel_r))

    hide = "\x1b[?25l"; show = "\x1b[?25h"; clear = "\x1b[2J"; home = "\x1b[H"
    sys.stdout.write(hide + clear); sys.stdout.flush()

    bg_fill = (4, 8, 10) if args.color else None
    soft = 6.0
    frame = 0
    try:
        while True:
            # clear & decay trails
            for y in range(micro_h):
                row = micro[y]
                for x in range(micro_w):
                    row[x] *= args.decay
            mb = max(0.0, min(1.0, args.micro_blur))*0.20
            if mb > 0 and (frame % 2 == 0):
                for y in range(1, micro_h-1):
                    up = micro[y-1]; row = micro[y]; dn = micro[y+1]
                    for x in range(1, micro_w-1):
                        row[x] = (1.0-mb)*row[x] + mb*(up[x]+dn[x]+row[x-1]+row[x+1])*0.25

            # physics
            step(stars, holes, novas, micro_w, micro_h, grid,
                 repel=args.repel, repel_r=args.repel_r, friction=args.friction,
                 bh_grav=args.bh_grav, soft=soft, dt=1.0, vmax=6.0)

            # random nova
            if random.random() < args.supernova_rate:
                if random.random() < 0.5 and holes:
                    bh = random.choice(holes); nx, ny = bh.x, bh.y
                else:
                    nx, ny = random.random()*micro_w, random.random()*micro_h
                novas.append(Supernova(nx, ny, strength=args.nova_strength, radius=args.nova_radius, ttl=args.nova_ttl))

            # deposit (safe-wrapped indices)
            for s in stars:
                ix = int(s.x) % micro_w
                iy = int(s.y) % micro_h
                fx = s.x - int(s.x); fy = s.y - int(s.y)
                x1 = (ix + 1) % micro_w; y1 = (iy + 1) % micro_h
                w00 = (1-fx)*(1-fy); w10 = fx*(1-fy); w01 = (1-fx)*fy; w11 = fx*fy
                e = 1.5
                micro[iy][ix]       += e * w00
                micro[iy][x1]       += e * w10
                micro[y1][ix]       += e * w01
                micro[y1][x1]       += e * w11

            if args.color:
                for ry in range(rows):
                    for rx in range(cols):
                        hue_field[ry][rx] = (0.995*hue_field[ry][rx] + 0.005*random.random()) % 1.0

            # render
            frame_text = render_frame(micro, cols, rows, gain=args.gain, gamma=args.gamma,
                                      color=args.color, hue_field=hue_field, bg=bg_fill)
            sys.stdout.write(home + frame_text + "\n"); sys.stdout.flush()

            frame += 1
            if args.rows and frame >= args.rows:
                break
            if args.delay > 0:
                time.sleep(args.delay)

            # resize
            new_cols, new_lines = shutil.get_terminal_size(fallback=(term_cols, term_lines))
            if new_cols != term_cols or new_lines != term_lines:
                term_cols, term_lines = new_cols, new_lines
                rows = max(6, term_lines - 2); cols = max(60, term_cols)
                micro_w = cols * 2; micro_h = rows * 4
                micro = [[0.0 for _ in range(micro_w)] for _ in range(micro_h)]
                hue_field = [[random.random() for _ in range(cols)] for _ in range(rows)]
                for bh in holes:
                    bh.x %= micro_w; bh.y %= micro_h
                grid = HashGrid(micro_w, micro_h, cell=max(4.0, args.repel_r))

    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\x1b[0m" + show + "\n"); sys.stdout.flush()

if __name__ == "__main__":
    main()
