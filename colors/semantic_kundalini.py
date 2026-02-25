
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
semantic_kundalini.py — emergent semantic attractors + kundalini continuum
Stdlib-only, truecolor ANSI, auto-width, background-space by default.
If your terminal hides bg colors, use --fg or --no-ansi.
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

def circ_mean_deg(weights, degs):
    sx = sy = 0.0
    for w,d in zip(weights,degs):
        a = math.radians(d)
        sx += w*math.cos(a); sy += w*math.sin(a)
    if sx == 0 and sy == 0: return 0.0
    return (math.degrees(math.atan2(sy, sx)) + 360.0) % 360.0

def unit(vec):
    n = sum(x*x for x in vec) ** 0.5
    if n == 0: return vec[:]
    return [x/n for x in vec]

def dot(a,b): return sum(x*y for x,y in zip(a,b))

def relu(x): return x if x>0 else 0.0

class Feature:
    __slots__ = ("u","pos","vel","hue_deg","name")
    def __init__(self, u, pos, vel, hue_deg, name=""):
        self.u = unit(u)
        self.pos = float(pos)
        self.vel = float(vel)
        self.hue_deg = float(hue_deg)%360.0
        self.name = name

def wrap_dist_signed(i, j, W):
    d = (j - i) % W
    if d > W/2: d -= W
    return d

def main():
    ap = argparse.ArgumentParser(description="Semantic attractors + kundalini continuum (1-D ring)")
    ap.add_argument("--fps", type=float, default=54.0)
    ap.add_argument("--width", type=int, default=0)
    ap.add_argument("--margin", type=int, default=1)
    ap.add_argument("--frames", type=int, default=0)
    ap.add_argument("--fg", action="store_true")
    ap.add_argument("--glyph", type=str, default="█")
    ap.add_argument("--no-ansi", action="store_true")
    ap.add_argument("--val", type=float, default=0.98)
    ap.add_argument("--sat-min", type=float, default=0.68)
    ap.add_argument("--sat-max", type=float, default=0.96)
    ap.add_argument("--latent-dim", type=int, default=8)
    ap.add_argument("--features", type=int, default=10)
    ap.add_argument("--topk", type=int, default=3)
    ap.add_argument("--feat-sigma", type=float, default=16.0)
    ap.add_argument("--feat-strength", type=float, default=1.0)
    ap.add_argument("--drift", type=float, default=0.006)
    ap.add_argument("--step", type=float, default=0.02)
    ap.add_argument("--momentum", type=float, default=0.85)
    ap.add_argument("--k-coils", type=float, default=1.5)
    ap.add_argument("--k-speed", type=float, default=0.025)
    ap.add_argument("--k-amp", type=float, default=0.25)
    ap.add_argument("--k-hue", type=float, default=12.0)
    ap.add_argument("--waves", type=int, default=3)
    ap.add_argument("--wave-drift", type=float, default=0.003)
    ap.add_argument("--scroll", type=float, default=0.16)
    args = ap.parse_args()

    W = args.width if args.width>0 else term_width(args.margin)
    use_bg = (not args.fg) and (not args.no_ansi)
    use_fg = (args.fg and not args.no_ansi)
    ascii_mode = args.no_ansi
    glyph = args.glyph[0] if args.glyph else "█"

    names = ["flow","edge","memory","rupture","resonance","ascent","grounding","mirror","coil","breath","spark","drift"]

    feats = []
    for i in range(args.features):
        u = [random.uniform(-1,1) for _ in range(args.latent_dim)]
        ang = math.degrees(math.atan2(u[1], u[0])) if args.latent_dim>=2 else random.uniform(0,360)
        hue = (ang + 360.0) % 360.0
        pos = random.uniform(0, W)
        vel = random.uniform(-args.drift, args.drift)
        feats.append(Feature(u=u, pos=pos, vel=vel, hue_deg=hue, name=names[i%len(names)]))

    waves = []
    for k in range(max(1,args.waves)):
        freq = random.uniform(0.15, 0.6)
        phase = random.random()*2*math.pi
        dim = k % max(1,args.latent_dim)
        amp = random.uniform(0.6, 1.2)
        waves.append(dict(freq=freq, phase=phase, dim=dim, amp=amp))

    dt = 1.0 / max(1.0, args.fps)
    frame = 0
    idx_phase = 0.0
    k_phase = random.random()*2*math.pi

    def gaussian(x, mu, sigma):
        z = (x-mu)/max(1e-9, sigma)
        return math.exp(-0.5*z*z)

    sys.stdout.write(f"[semantic_kundalini] W={W} D={args.latent_dim} F={len(feats)} ansi={'off' if ascii_mode else 'on'} mode={'bg' if use_bg else ('fg' if use_fg else 'ascii')}\n")
    sys.stdout.flush()

    try:
        while True:
            if args.frames>0 and frame >= args.frames:
                break

            idx_phase = (idx_phase + args.scroll) % W
            k_phase += args.k_speed

            total_act = [0.0]*W
            hue_mix_deg = [0.0]*W
            hue_mix_w   = [0.0]*W

            base_ctx = [[0.0]*W for _ in range(min(3, args.latent_dim))]
            for w in waves:
                w["phase"] += args.wave_drift
                dim = min(w["dim"], len(base_ctx)-1) if base_ctx else 0
                for i in range(W):
                    x = ((i + idx_phase) % W)/W
                    base_ctx[dim][i] += w["amp"] * math.sin(2*math.pi*w["freq"]*x + w["phase"])

            k_coil = [0.0]*W
            for i in range(W):
                x = ((i + idx_phase) % W)/W
                k_coil[i] = 0.5 + 0.5*math.sin(2*math.pi*args.k_coils*x + k_phase)

            for f in feats:
                span = int(max(3, 3*args.feat_sigma))
                for dj in range(-span, span+1):
                    j = int((f.pos + dj) % W)
                    w = args.feat_strength * gaussian(j, f.pos, args.feat_sigma)
                    if args.latent_dim >= 1: base_ctx[0][j] += w * f.u[0]
                    if args.latent_dim >= 2: base_ctx[1][j] += w * f.u[1]
                    if args.latent_dim >= 3: base_ctx[2][j] += w * f.u[2]

            for i in range(W):
                v = [0.0]*args.latent_dim
                if args.latent_dim>=1: v[0] = base_ctx[0][i]
                if args.latent_dim>=2: v[1] = base_ctx[1][i]
                if args.latent_dim>=3: v[2] = base_ctx[2][i]

                best = []
                for f in feats:
                    a = relu(dot(f.u, v))
                    if a>0:
                        best.append((a, f.hue_deg))
                if best:
                    best.sort(reverse=True)
                    best = best[:max(1,args.topk)]
                    weights = [a for (a,_) in best]
                    hues    = [h for (_,h) in best]
                    h_deg = circ_mean_deg(weights, hues)
                    wsum = sum(weights)
                    hue_mix_deg[i] = h_deg
                    total_act[i] = wsum
                    hue_mix_w[i] = max(hue_mix_w[i], wsum)
                else:
                    total_act[i] = 0.0
                    hue_mix_deg[i] = 0.0
                    hue_mix_w[i] = 0.0

            for f in feats:
                delta = 3.5
                def local_act(pos):
                    j = int(pos % W)
                    jp = (j+1)%W; jm = (j-1)%W
                    return 0.25*hue_mix_w[jm] + 0.5*hue_mix_w[j] + 0.25*hue_mix_w[jp]
                g = (local_act(f.pos+delta) - local_act(f.pos-delta)) / (2*delta)
                f.vel = args.momentum*f.vel + args.step * g + random.uniform(-args.drift, args.drift)*0.1
                f.pos = (f.pos + f.vel) % W

            out = []
            last = None
            for i in range(W):
                h_deg = hue_mix_deg[i]
                h_deg = (h_deg + args.k_hue * (k_coil[i]-0.5)*2.0) % 360.0
                s = args.sat_min + (args.sat_max-args.sat_min) * min(1.0, total_act[i])
                s = s * (1.0 - args.k_amp*0.3 + args.k_amp*0.3 * k_coil[i])
                v = args.val * (0.85 - 0.25*args.k_amp + 0.25*args.k_amp * (0.5 + 0.5*k_coil[i]))
                if args.no_ansi:
                    ramp = " .:-=+*#%@"
                    intensity = s*v
                    ch = ramp[int(max(0,min(len(ramp)-1, int(intensity*(len(ramp)-1)))))]
                    out.append(ch)
                else:
                    r,g,b = hsv_to_rgb(h_deg/360.0, max(0.0,min(1.0,s)), max(0.0,min(1.0,v)))
                    if use_bg:
                        if last != (r,g,b): out.append(bg(r,g,b)); last=(r,g,b)
                        out.append(" ")
                    else:
                        out.append(fg(r,g,b) + glyph)

            if not args.no_ansi:
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
