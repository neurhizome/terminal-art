
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
aurora_gliders.py — sparse gliders, cumulative trails, aurora mixing

What it does
- A small number of "gliders" orbit on a 1‑D ring (auto‑width).
- Each glider carries a hue and deposits a soft trail (hue vector field).
- Trails decay slowly and diffuse, so the ambient field remembers passage.
- Optional "gravity" attractors bias glider velocity along the ring.
- Background truecolor (space glyph) by default—good for iPhone terminals.

Stdlib only.
"""

import sys, time, math, random, argparse, shutil

ESC   = "\x1b["
RESET = "\x1b[0m"

# -------------------- ANSI helpers --------------------

def bg(r,g,b): return f"\x1b[48;2;{int(r)};{int(g)};{int(b)}m"
def fg(r,g,b): return f"\x1b[38;2;{int(r)};{int(g)};{int(b)}m"

def term_width(margin:int=1) -> int:
    cols = shutil.get_terminal_size((80,24)).columns
    return max(20, cols - margin)

# -------------------- Color math ----------------------

def hsv_to_rgb(h, s, v):
    # h in [0,1), s,v in [0,1]
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

# -------------------- Engine --------------------------

def gaussian(x, mu, sigma):
    z = (x-mu)/max(1e-9, sigma)
    return math.exp(-0.5*z*z)

class Glider:
    def __init__(self, pos, vel, hue_deg, life):
        self.pos = float(pos)
        self.vel = float(vel)
        self.hue_deg = float(hue_deg) % 360.0
        self.life = int(life)
        self.age  = 0

    def alive(self): return self.age < self.life

def wrap_dist(i, j, W):
    """Shortest signed distance along ring from i -> j."""
    d = (j - i) % W
    if d > W/2: d -= W
    return d

def main():
    ap = argparse.ArgumentParser(description="Sparse aurora gliders on a 1-D ring")
    # timing / geometry
    ap.add_argument("--fps", type=float, default=54.0)
    ap.add_argument("--width", type=int, default=0)
    ap.add_argument("--margin", type=int, default=1)
    # render
    ap.add_argument("--fg", action="store_true", help="use foreground glyph instead of background space")
    ap.add_argument("--glyph", type=str, default="█")
    ap.add_argument("--val", type=float, default=0.98)
    ap.add_argument("--sat-min", type=float, default=0.70)
    ap.add_argument("--sat-max", type=float, default=0.96)
    # gliders
    ap.add_argument("--gliders", type=int, default=4)
    ap.add_argument("--spawn", type=float, default=0.02, help="spawn probability per frame if below target count")
    ap.add_argument("--life", type=int, nargs=2, default=[220, 520])
    ap.add_argument("--speed", type=float, nargs=2, default=[0.15, 0.60])
    ap.add_argument("--cool-hues", action="store_true", help="limit glider hues to cool palette")
    # trails / ambient memory
    ap.add_argument("--trail-sigma", type=float, default=10.0, help="gaussian width of deposit (pixels)")
    ap.add_argument("--trail-gain", type=float, default=0.9, help="deposit strength")
    ap.add_argument("--trail-decay", type=float, default=0.992, help="per-frame multiplicative decay [0..1]")
    ap.add_argument("--trail-diff", type=float, default=0.08, help="diffusion of trails [0..1]")
    # gravity / attractors
    ap.add_argument("--attractors", type=int, default=3, help="gravitational attractors along ring")
    ap.add_argument("--grav", type=float, default=0.004, help="acceleration toward nearest attractor")
    ap.add_argument("--friction", type=float, default=0.0008, help="velocity damping per frame")
    ap.add_argument("--attr-drift", type=float, default=0.003, help="slow drift of attractor positions")
    # base aurora field
    ap.add_argument("--base-amp", type=float, default=0.25, help="weight of ambient hue waves vs trails")
    ap.add_argument("--waves", type=int, default=2, help="ambient long waves")
    ap.add_argument("--wave-drift", type=float, default=0.003, help="phase drift of ambient waves")
    # diagonals
    ap.add_argument("--scroll", type=float, default=0.12, help="index phase per frame (diagonal slope)")
    # duration
    ap.add_argument("--duration", type=float, default=0.0)
    args = ap.parse_args()

    # geometry
    W = args.width if args.width>0 else term_width(args.margin)
    use_bg = not args.fg
    glyph = args.glyph[0] if args.glyph else "█"

    # trail hue-vector fields and sat boost
    hx = [0.0]*W; hy = [0.0]*W; sboost = [0.0]*W

    # ambient long waves (cool aurora bias)
    waves = []
    base_pool = [180,190,205,220,240,260,280,300,320]
    for k in range(max(1,args.waves)):
        hue_deg = random.choice(base_pool) + random.uniform(-10,10)
        freq = random.uniform(0.2, 0.8)   # cycles around ring
        phase = random.random()*2*math.pi
        waves.append(dict(hue_deg=hue_deg, freq=freq, phase=phase))

    # attractors (positions along ring)
    attrs = [random.uniform(0, W) for _ in range(max(0, args.attractors))]

    # initial gliders sparse
    gliders = []
    def spawn_one():
        hue_deg = (random.choice(base_pool) if args.cool_hues else random.uniform(0,360)) + random.uniform(-12,12)
        vel = random.uniform(args.speed[0], args.speed[1]) * random.choice([-1,1])
        life = random.randint(args.life[0], args.life[1])
        pos = random.uniform(0, W)
        gliders.append(Glider(pos, vel, hue_deg, life))

    for _ in range(min(args.gliders, 2)):  # start very sparse
        spawn_one()

    # timing
    dt = 1.0 / max(1.0, args.fps)
    t0 = time.perf_counter()
    phase = 0.0

    # run
    try:
        elapsed = 0.0
        while True:
            # end?
            if args.duration>0 and elapsed >= args.duration:
                break

            # diagonal slope for waterfall view
            phase = (phase + args.scroll) % W

            # drift attractors slowly (creates orbital feel)
            for i in range(len(attrs)):
                attrs[i] = (attrs[i] + random.uniform(-args.attr_drift, args.attr_drift)) % W

            # update gliders: grav acceleration + friction, move, deposit trails
            keep = []
            for g in gliders:
                # gravity toward nearest attractor (if any)
                if attrs:
                    # choose attractor with minimal wrap distance
                    j = min(range(len(attrs)), key=lambda k: abs(wrap_dist(g.pos, attrs[k], W)))
                    d = wrap_dist(g.pos, attrs[j], W)  # signed
                    acc = args.grav * max(-1.0, min(1.0, d / (W*0.25)))  # gentle
                    g.vel += acc

                # friction
                if g.vel > 0:
                    g.vel = max(0.0, g.vel - args.friction)
                elif g.vel < 0:
                    g.vel = min(0.0, g.vel + args.friction)

                # move
                g.pos = (g.pos + g.vel) % W
                g.age += 1

                # deposit gaussian hue vector + saturation boost
                u = math.cos(math.radians(g.hue_deg)); v = math.sin(math.radians(g.hue_deg))
                center = g.pos; sig = args.trail_sigma
                span = int(max(3, 3*sig))
                for dj in range(-span, span+1):
                    j = int((center + dj) % W)
                    w = args.trail_gain * gaussian(j, center, sig)
                    hx[j] += w * u
                    hy[j] += w * v
                    sboost[j] = min(1.0, sboost[j] + 0.5*w)

                if g.alive():
                    keep.append(g)
            gliders = keep

            # sparse spawning
            if len(gliders) < args.gliders and random.random() < args.spawn:
                spawn_one()

            # trail decay + diffusion (ambient memory)
            # decay
            decay = max(0.90, min(0.9999, args.trail_decay))
            for i in range(W):
                hx[i] *= decay; hy[i] *= decay; sboost[i] *= decay
            # diffusion (3-tap)
            if args.trail_diff > 0.0:
                a = max(0.0, min(1.0, args.trail_diff))
                hx2 = [0.0]*W; hy2 = [0.0]*W; sb2=[0.0]*W
                for i in range(W):
                    L = (i-1) % W; R = (i+1)%W
                    hx2[i] = hx[i]*(1-2*a) + a*(hx[L]+hx[R])
                    hy2[i] = hy[i]*(1-2*a) + a*(hy[L]+hy[R])
                    sb2[i] = sboost[i]*(1-2*a) + a*(sboost[L]+sboost[R])
                hx,hy,sboost = hx2,hy2,sb2

            # ambient aurora base hue from long waves
            # build a small vector from weighted wave hues
            base_vx = [0.0]*W; base_vy=[0.0]*W
            for w in waves:
                w["phase"] += args.wave_drift
                ang = math.radians(w["hue_deg"])
                ux,uy = math.cos(ang), math.sin(ang)
                f = w["freq"]
                for i in range(W):
                    x = (i + phase) / W
                    amp = 0.5 + 0.5*math.sin(2*math.pi*f*x + w["phase"])  # [0,1]
                    base_vx[i] += amp * ux
                    base_vy[i] += amp * uy

            # mix trails and base to color line
            out = []
            last = None
            for i in range(W):
                # composite hue vector
                vx = hx[i] + args.base_amp * base_vx[i]
                vy = hy[i] + args.base_amp * base_vy[i]
                if vx == 0.0 and vy == 0.0:
                    h = 0.0; s=0.0
                else:
                    h = (math.degrees(math.atan2(vy, vx)) + 360.0) % 360.0
                    h = (h / 360.0) % 1.0
                    # saturation rises with trail strength
                    mag = min(1.0, (abs(hx[i]) + abs(hy[i])) * 0.9)
                    s = args.sat_min + (args.sat_max - args.sat_min) * max(mag, sboost[i])

                r,g,b = hsv_to_rgb(h, s, args.val)
                if use_bg:
                    if last != (r,g,b): out.append(bg(r,g,b)); last=(r,g,b)
                    out.append(" ")
                else:
                    out.append(fg(r,g,b) + glyph)

            out.append(RESET + "\n")
            sys.stdout.write("".join(out)); sys.stdout.flush()

            # pacing
            t0 += dt
            sleep_for = t0 - time.perf_counter()
            if sleep_for > 0: time.sleep(sleep_for)
            else: t0 = time.perf_counter()

            elapsed += dt

    except KeyboardInterrupt:
        pass
