#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
manifold_galaxies.py — emergent galaxies on a 1‑D ring
Stdlib‑only. Auto‑width. Background‑space by default. Use --fg or --no-ansi if needed.
"""
import sys, time, math, random, argparse, shutil

ESC   = "\x1b["
RESET = "\x1b[0m"

def term_width(margin:int=1) -> int:
    try:
        cols = shutil.get_terminal_size((80,24)).columns
    except Exception:
        cols = 80
    return max(20, cols - max(0, margin))

def bg(r,g,b): return f"\x1b[48;2;{int(r)};{int(g)};{int(b)}m"
def fg(r,g,b): return f"\x1b[38;2;{int(r)};{int(g)};{int(b)}m"

def hsv_to_rgb(h, s, v):
    if s <= 0.0:
        c = int(255*v); return c,c,c
    h = (h % 1.0) * 6.0
    i = int(h); f = h - i
    p = v*(1-s); q = v*(1-s*f); t = v*(1 - s*(1-f))
    if   i == 0: r,g,b = v,t,p
    elif i == 1: r,g,b = q,v,p
    elif i == 2: r,g,b = p,v,t
    elif i == 3: r,g,b = p,q,v
    elif i == 4: r,g,b = t,p,v
    else:        r,g,b = v,p,q
    return int(255*r), int(255*g), int(255*b)

class Clifford:
    def __init__(self, a=1.7, b=-1.3, c=-0.1, d=-1.2, seed=None):
        self.a, self.b, self.c, self.d = a,b,c,d
        self.x = 0.1 if seed is None else seed[0]
        self.y = 0.0 if seed is None else seed[1]
    def step(self):
        x,y = self.x, self.y
        nx = math.sin(self.a*y) + self.c*math.cos(self.a*x)
        ny = math.sin(self.b*x) + self.d*math.cos(self.b*y)
        self.x, self.y = nx, ny
        return nx, ny

class Ikeda:
    def __init__(self, u=0.918, x=0.1, y=0.0):
        self.u = u; self.x=x; self.y=y
    def step(self):
        x,y = self.x, self.y
        t = 0.4 - 6.0/(1.0 + x*x + y*y)
        nx = 1 + self.u * (x*math.cos(t) - y*math.sin(t))
        ny = self.u * (x*math.sin(t) + y*math.cos(t))
        self.x, self.y = nx, ny
        return nx, ny

class PolygonField:
    def __init__(self, sides=6, sigma=0.20, rot_speed=0.4):
        self.sides = max(3,int(sides))
        self.sigma = max(0.02, float(sigma))
        self.theta = 0.0
        self.rot_speed = float(rot_speed)
    def step(self):
        self.theta += self.rot_speed
    def weight_at_angle(self, ang):
        w = 0.0
        for k in range(self.sides):
            center = self.theta + 2*math.pi*k/self.sides
            d = math.atan2(math.sin(ang-center), math.cos(ang-center))
            w += math.exp(-0.5*(d/self.sigma)**2)
        return w

def smooth3(arr, W, a):
    if a <= 1e-9: return arr[:]
    out = [0.0]*W
    for i in range(W):
        L = (i-1)%W; R=(i+1)%W
        out[i] = arr[i]*(1-2*a) + a*(arr[L]+arr[R])
    return out

def palette_rgb(h_norm, s, v, palette):
    if palette == "cool":
        h = (0.55 + 0.55*h_norm) % 1.0
    elif palette == "aurora":
        h = (0.50 + 0.35*h_norm) % 1.0
    elif palette == "fire":
        h = (0.02 + 0.12*h_norm) % 1.0
    elif palette == "ice":
        h = (0.55 + 0.20*h_norm) % 1.0
    else:
        h = h_norm % 1.0
    return hsv_to_rgb(h, s, v)

def main():
    ap = argparse.ArgumentParser(description="Manifold galaxies on a 1-D ring")
    ap.add_argument("--fps", type=float, default=56.0)
    ap.add_argument("--frames", type=int, default=0)
    ap.add_argument("--width", type=int, default=0)
    ap.add_argument("--margin", type=int, default=1)
    ap.add_argument("--fg", action="store_true")
    ap.add_argument("--glyph", type=str, default="█")
    ap.add_argument("--no-ansi", action="store_true")
    ap.add_argument("--val", type=float, default=0.99)
    ap.add_argument("--sat-min", type=float, default=0.65)
    ap.add_argument("--sat-max", type=float, default=0.98)
    ap.add_argument("--palette", type=str, default="aurora",
                    choices=["rainbow","cool","aurora","fire","ice"])
    ap.add_argument("--timewarp", type=float, default=3.0)
    ap.add_argument("--decay", type=float, default=0.992)
    ap.add_argument("--smooth", type=float, default=0.08)
    ap.add_argument("--rot", type=float, default=0.18)
    ap.add_argument("--twist", type=float, default=0.25)
    ap.add_argument("--gate", type=float, default=0.00)
    ap.add_argument("--gate-noise", type=float, default=0.00)
    ap.add_argument("--manifold", type=str, default="clifford",
                    choices=["clifford","ikeda","polygon","rings"])
    ap.add_argument("--samples", type=int, default=800)
    ap.add_argument("--a", type=float, default=1.7)
    ap.add_argument("--b", type=float, default=-1.3)
    ap.add_argument("--c", type=float, default=-0.1)
    ap.add_argument("--d", type=float, default=-1.2)
    ap.add_argument("--u", type=float, default=0.918)
    ap.add_argument("--sides", type=int, default=6)
    ap.add_argument("--poly-sigma", type=float, default=0.25)
    ap.add_argument("--poly-speed", type=float, default=0.12)
    ap.add_argument("--rings", type=int, default=4)
    ap.add_argument("--ring-sigma", type=float, default=0.20)
    ap.add_argument("--ring-wander", type=float, default=0.05)
    args = ap.parse_args()

    W = args.width if args.width>0 else term_width(args.margin)
    use_bg = (not args.fg) and (not args.no_ansi)
    use_fg = (args.fg and not args.no_ansi)
    ascii_mode = args.no_ansi
    glyph = args.glyph[0] if args.glyph else "█"

    H = [0.0]*W
    hue_phase = 0.0

    if args.manifold == "clifford":
        M = Clifford(a=args.a, b=args.b, c=args.c, d=args.d)
    elif args.manifold == "ikeda":
        M = Ikeda(u=args.u)
    elif args.manifold == "polygon":
        M = PolygonField(sides=args.sides, sigma=args.poly_sigma, rot_speed=args.poly_speed)
    else:
        centers = [random.random() for _ in range(max(1,args.rings))]

    ramp = " .:-=+*#%@"
    dt = 1.0 / max(1.0, args.fps)
    frame = 0

    sys.stdout.write(f"[manifold_galaxies] W={W} palette={args.palette} mode={'bg' if use_bg else ('fg' if use_fg else 'ascii')} manifold={args.manifold}\n")
    sys.stdout.flush()

    try:
        while True:
            if args.frames>0 and frame >= args.frames:
                break

            H = [h*args.decay for h in H]
            if args.smooth>0:
                H = smooth3(H, W, args.smooth)

            steps = max(1, int(args.samples * max(0.1, args.timewarp)))
            if args.manifold in ("clifford","ikeda"):
                for _ in range(steps):
                    x,y = M.step()
                    ang = math.atan2(y, x) + hue_phase*0.25
                    frac = (ang % (2*math.pi)) / (2*math.pi)
                    idx = int(frac * W) % W
                    H[idx] += 1.0
            elif args.manifold == "polygon":
                M.step()
                for k in range(steps):
                    ang = 2*math.pi*(k/steps)
                    w = M.weight_at_angle(ang)
                    frac = (ang % (2*math.pi)) / (2*math.pi)
                    idx = int(frac * W) % W
                    H[idx] += w
            else:
                centers = [(c + random.uniform(-args.ring_wander, args.ring_wander)) % 1.0 for c in centers]
                for _ in range(max(1,steps//4)):
                    for c in centers:
                        ang = 2*math.pi*c
                        frac = (ang % (2*math.pi)) / (2*math.pi)
                        idx_c = frac * W
                        span = max(3, int(3*args.ring_sigma*W))
                        for dj in range(-span, span+1):
                            j = int((idx_c + dj) % W)
                            d = (dj / max(1.0, args.ring_sigma*W))
                            H[j] += math.exp(-0.5*d*d)

            srt = sorted(H)
            hi = srt[int(0.98*len(srt))]
            scale = max(1e-6, hi)
            F = [min(1.0, h/scale) for h in H]

            hue_phase = (hue_phase + args.rot) % 1.0

            if args.gate>0.0 or args.gate_noise>0.0:
                base = args.gate
                G = [base + (random.random()-0.5)*2*args.gate_noise for _ in range(W)]
            else:
                G = [0.0]*W

            out = []
            last = None
            for i,f in enumerate(F):
                h = (hue_phase + i/W + args.twist*(f-0.5)) % 1.0
                s = args.sat_min + (args.sat_max-args.sat_min)*f
                v = args.val
                if ascii_mode:
                    ch = ramp[int((s*v)*(len(ramp)-1))]
                    out.append(ch)
                else:
                    if f < G[i]:
                        r,g,b = 0,0,0
                    else:
                        r,g,b = palette_rgb(h, s, v, args.palette)
                    if use_bg:
                        if last != (r,g,b): out.append(bg(r,g,b)); last=(r,g,b)
                        out.append(" ")
                    else:
                        out.append(fg(r,g,b)+glyph)

            if not ascii_mode:
                out.append(RESET)
            out.append("\n")
            sys.stdout.write("".join(out)); sys.stdout.flush()

            frame += 1
            time.sleep(dt)

    except KeyboardInterrupt:
        if not ascii_mode:
            sys.stdout.write(RESET)
        pass

if __name__ == "__main__":
    main()
