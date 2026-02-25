
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
aurora_gliders_v2.py — sparse auroras with cumulative trails
Robust output: supports foreground mode and an ASCII fallback (no ANSI).

Key flags:
  --frames N      Run exactly N frames then exit (helps confirm output)
  --fg            Use colored glyphs instead of bg spaces
  --glyph "█"     Choose glyph for --fg
  --no-ansi       Disable ANSI entirely; prints ASCII shades (.,:-=+*#%@)
"""

import sys, time, math, random, argparse, shutil, os

ESC   = "\x1b["
RESET = "\x1b[0m"

def term_width(margin:int=1) -> int:
    try:
        cols = shutil.get_terminal_size((80,24)).columns
    except Exception:
        cols = 80
    # shave margin to avoid wrap; keep minimum
    return max(20, cols - max(0, margin))

def bg(r,g,b): return f"{ESC}48;2;{int(r)};{int(g)};{int(b)}m"
def fg(r,g,b): return f"{ESC}38;2;{int(r)};{int(g)};{int(b)}m"

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

def gaussian(x, mu, sigma):
    z = (x-mu)/max(1e-9, sigma)
    return math.exp(-0.5*z*z)

class Glider:
    def __init__(self, pos, vel, hue_deg, life):
        self.pos = float(pos)
        self.vel = float(vel)
        self.hue_deg = float(hue_deg) % 360.0
        self.life = int(life); self.age = 0
    def alive(self): return self.age < self.life

def wrap_dist(i, j, W):
    d = (j - i) % W
    if d > W/2: d -= W
    return d

def main():
    ap = argparse.ArgumentParser(description="Sparse aurora gliders (robust output)")
    # timing / geometry
    ap.add_argument("--fps", type=float, default=54.0)
    ap.add_argument("--width", type=int, default=0)
    ap.add_argument("--margin", type=int, default=1)
    ap.add_argument("--frames", type=int, default=0, help="number of frames to render (0=infinite)")
    # render
    ap.add_argument("--fg", action="store_true", help="use foreground glyph instead of background space")
    ap.add_argument("--glyph", type=str, default="█")
    ap.add_argument("--no-ansi", action="store_true", help="disable ANSI; ASCII fallback")
    ap.add_argument("--val", type=float, default=0.98)
    ap.add_argument("--sat-min", type=float, default=0.70)
    ap.add_argument("--sat-max", type=float, default=0.96)
    # gliders
    ap.add_argument("--gliders", type=int, default=4)
    ap.add_argument("--spawn", type=float, default=0.02)
    ap.add_argument("--life", type=int, nargs=2, default=[220, 520])
    ap.add_argument("--speed", type=float, nargs=2, default=[0.15, 0.60])
    ap.add_argument("--cool-hues", action="store_true")
    # trails / ambient
    ap.add_argument("--trail-sigma", type=float, default=10.0)
    ap.add_argument("--trail-gain", type=float, default=0.9)
    ap.add_argument("--trail-decay", type=float, default=0.994)
    ap.add_argument("--trail-diff", type=float, default=0.08)
    # gravity
    ap.add_argument("--attractors", type=int, default=3)
    ap.add_argument("--grav", type=float, default=0.004)
    ap.add_argument("--friction", type=float, default=0.0008)
    ap.add_argument("--attr-drift", type=float, default=0.003)
    # base aurora field
    ap.add_argument("--base-amp", type=float, default=0.25)
    ap.add_argument("--waves", type=int, default=2)
    ap.add_argument("--wave-drift", type=float, default=0.003)
    # diagonals
    ap.add_argument("--scroll", type=float, default=0.12)
    args = ap.parse_args()

    # geometry
    W = args.width if args.width>0 else term_width(args.margin)
    use_bg = (not args.fg) and (not args.no_ansi)
    use_fg = (args.fg and not args.no_ansi)
    ascii_mode = args.no_ansi
    glyph = args.glyph[0] if args.glyph else "█"

    # state fields
    hx = [0.0]*W; hy = [0.0]*W; sboost = [0.0]*W

    # ambient waves
    base_pool = [180,190,205,220,240,260,280,300,320]
    waves = []
    for k in range(max(1,args.waves)):
        hue_deg = random.choice(base_pool) + random.uniform(-10,10)
        freq = random.uniform(0.2, 0.8)
        phase = random.random()*2*math.pi
        waves.append(dict(hue_deg=hue_deg, freq=freq, phase=phase))

    # attractors
    attrs = [random.uniform(0, W) for _ in range(max(0,args.attractors))]

    # gliders
    gliders = []
    def spawn_one():
        hue_deg = (random.choice(base_pool) if args.cool_hues else random.uniform(0,360)) + random.uniform(-12,12)
        vel = random.uniform(args.speed[0], args.speed[1]) * random.choice([-1,1])
        life = random.randint(args.life[0], args.life[1])
        pos = random.uniform(0, W)
        gliders.append(Glider(pos, vel, hue_deg, life))

    # start super sparse
    for _ in range(min(args.gliders, 2)):
        spawn_one()

    # timing
    dt = 1.0 / max(1.0, args.fps)
    next_t = time.perf_counter() + dt

    # ASCII ramp
    ramp = " .:-=+*#%@"
    try:
        # debug banner (always visible even in ASCII)
        sys.stdout.write(f"[aurora_gliders] W={W} fps={args.fps} ansi={'off' if ascii_mode else 'on'} mode={'bg' if use_bg else ('fg' if use_fg else 'ascii')} gliders={len(gliders)}\n")
        sys.stdout.flush()

        frame = 0
        phase = 0.0
        while True:
            if args.frames>0 and frame >= args.frames:
                break

            # diagonal slope
            phase = (phase + args.scroll) % W

            # drift attractors
            for i in range(len(attrs)):
                attrs[i] = (attrs[i] + random.uniform(-args.attr_drift, args.attr_drift)) % W

            # update gliders + deposit trails
            keep = []
            for g in gliders:
                if attrs:
                    j = min(range(len(attrs)), key=lambda k: abs(wrap_dist(g.pos, attrs[k], W)))
                    d = wrap_dist(g.pos, attrs[j], W)
                    g.vel += args.grav * max(-1.0, min(1.0, d/(W*0.25)))
                # friction
                if g.vel > 0: g.vel = max(0.0, g.vel - args.friction)
                elif g.vel < 0: g.vel = min(0.0, g.vel + args.friction)

                g.pos = (g.pos + g.vel) % W
                g.age += 1

                u = math.cos(math.radians(g.hue_deg)); v = math.sin(math.radians(g.hue_deg))
                center = g.pos; sig = args.trail_sigma
                span = int(max(3, 3*sig))
                for dj in range(-span, span+1):
                    j = int((center + dj) % W)
                    w = args.trail_gain * gaussian(j, center, sig)
                    hx[j] += w * u; hy[j] += w * v
                    sboost[j] = min(1.0, sboost[j] + 0.5*w)

                if g.alive(): keep.append(g)
            gliders = keep

            if len(gliders) < args.gliders and random.random() < args.spawn:
                spawn_one()

            # decay + diffusion
            decay = max(0.90, min(0.9999, args.trail_decay))
            for i in range(W):
                hx[i] *= decay; hy[i] *= decay; sboost[i] *= decay
            a = max(0.0, min(1.0, args.trail_diff))
            if a > 0.0:
                hx2 = [0.0]*W; hy2 = [0.0]*W; sb2=[0.0]*W
                for i in range(W):
                    L = (i-1)%W; R=(i+1)%W
                    hx2[i] = hx[i]*(1-2*a) + a*(hx[L]+hx[R])
                    hy2[i] = hy[i]*(1-2*a) + a*(hy[L]+hy[R])
                    sb2[i] = sboost[i]*(1-2*a) + a*(sboost[L]+sboost[R])
                hx,hy,sboost = hx2,hy2,sb2

            # ambient base
            base_vx = [0.0]*W; base_vy=[0.0]*W
            for w in waves:
                w["phase"] += args.wave_drift
                ang = math.radians(w["hue_deg"]); ux,uy = math.cos(ang), math.sin(ang)
                f = w["freq"]
                for i in range(W):
                    x = (i + phase) / W
                    amp = 0.5 + 0.5*math.sin(2*math.pi*f*x + w["phase"])
                    base_vx[i] += amp * ux; base_vy[i] += amp * uy

            # compose line as RGB or ASCII
            out = []
            last = None
            for i in range(W):
                vx = hx[i] + args.base_amp*base_vx[i]
                vy = hy[i] + args.base_amp*base_vy[i]
                if vx == 0.0 and vy == 0.0:
                    h = 0.0; s = 0.0; mag = 0.0
                else:
                    h = (math.degrees(math.atan2(vy, vx)) + 360.0) % 360.0
                    h = (h/360.0)%1.0
                    mag = min(1.0, (abs(hx[i])+abs(hy[i]))*0.9)
                    s = args.sat_min + (args.sat_max-args.sat_min)*max(mag, sboost[i])
                if ascii_mode:
                    # grayscale intensity via saturation*value
                    intensity = s*args.val
                    ch = ramp[int(intensity*(len(ramp)-1))]
                    out.append(ch)
                elif use_bg:
                    r,g,b = hsv_to_rgb(h, s, args.val)
                    if last != (r,g,b): out.append(bg(r,g,b)); last=(r,g,b)
                    out.append(" ")
                else:  # fg glyphs
                    r,g,b = hsv_to_rgb(h, s, args.val)
                    out.append(fg(r,g,b)+glyph)

            if not ascii_mode:
                out.append(RESET)
            out.append("\n")
            sys.stdout.write("".join(out)); sys.stdout.flush()

            frame += 1
            # timing
            if args.frames>0 and frame >= args.frames:
                break
            # basic frame pacing
            now = time.perf_counter()
            sleep_for = next_t - now
            if sleep_for > 0: time.sleep(sleep_for)
            next_t += 1.0 / max(1.0, args.fps)

    except KeyboardInterrupt:
        if not ascii_mode:
            sys.stdout.write(RESET)
        pass

if __name__ == "__main__":
    main()
