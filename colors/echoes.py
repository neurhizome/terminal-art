#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
wraithframe.py — openWRAITHFRAME-inspired 1‑D ring color engine
"""
import sys, math, time, shutil, argparse, random, hashlib

ESC   = "\x1b["
RESET = "\x1b[0m"

def rgb_bg(r,g,b): return f"{ESC}48;2;{int(r)};{int(g)};{int(b)}m"
def rgb_fg(r,g,b): return f"{ESC}38;2;{int(r)};{int(g)};{int(b)}m"
def term_width(margin:int=1) -> int:
    cols = shutil.get_terminal_size((80,24)).columns
    return max(20, cols - margin)

def clamp01(x): return 0.0 if x < 0.0 else 1.0 if x > 1.0 else x
def clamp255(x): 
    x = 0 if x < 0 else (255 if x > 255 else x); 
    return int(x)

def hsv_to_rgb(h, s, v):
    if s <= 0.0:
        c = clamp255(255*v); return c,c,c
    h = (h % 1.0) * 6.0
    i = int(h); f = h - i
    p = v*(1-s); q = v*(1-s*f); t = v*(1 - s*(1-f))
    if   i == 0: r,g,b = v,t,p
    elif i == 1: r,g,b = q,v,p
    elif i == 2: r,g,b = p,v,t
    elif i == 3: r,g,b = p,q,v
    elif i == 4: r,g,b = t,p,v
    else:        r,g,b = v,p,q
    return clamp255(255*r), clamp255(255*g), clamp255(255*b)

def circ_lerp_deg(a, b, t):
    d = (b - a + 540.0) % 360.0 - 180.0
    return (a + d*t) % 360.0

def deg_mean(w, degs):
    sx = sy = 0.0
    for wi,di in zip(w,degs):
        ang = math.radians(di)
        sx += wi*math.cos(ang); sy += wi*math.sin(ang)
    if sx == 0 and sy == 0: return degs[0]
    return (math.degrees(math.atan2(sy, sx)) + 360.0) % 360.0

def sha_bits(row_rgb, segments=32):
    import struct
    q = bytearray()
    for (r,g,b) in row_rgb:
        q.append((r>>2)&0x3F); q.append((g>>2)&0x3F); q.append((b>>2)&0x3F)
    h = hashlib.sha256(q).digest()
    bits = []
    for byte in h:
        for k in range(8):
            bits.append((byte >> (7-k)) & 1)
    if segments <= 0: segments = 32
    return bits[:segments]

def gaussian(x, mu, sigma):
    z = (x-mu)/max(1e-9, sigma)
    return math.exp(-0.5*z*z)

class RotorCube:
    TETRA = [
        ( 1,  1,  1),
        ( 1, -1, -1),
        (-1,  1, -1),
        (-1, -1,  1),
    ]
    TETRA = [tuple(c/(3**0.5) for c in v) for v in TETRA]
    def __init__(self, x, dx, life, sigma, hue_deg, axis=(1,1,0), ang_speed=0.5):
        self.x = float(x); self.dx = float(dx)
        self.life = int(life); self.age = 0
        self.sigma = float(sigma)
        self.hue_deg = float(hue_deg)
        self.axis = axis; self.theta = random.random()*math.tau; self.ang_speed = ang_speed
    def alive(self): return self.age < self.life
    def step(self, W):
        self.x = (self.x + self.dx) % W
        self.theta += self.ang_speed
        self.age += 1
    def hue_field(self):
        ax = self.axis
        c = math.cos(self.theta); s = math.sin(self.theta)
        p = (c, s, 0.0)
        x,y,z = ax; n = (x*x+y*y+z*z)**0.5 or 1.0; x,y,z = x/n, y/n, z/n
        cA = math.cos(self.theta*0.3); sA = math.sin(self.theta*0.3); C = 1-cA
        R = (
            (cA + x*x*C,     x*y*C - z*sA,  x*z*C + y*sA),
            (y*x*C + z*sA,   cA + y*y*C,    y*z*C - x*sA),
            (z*x*C - y*sA,   z*y*C + x*sA,  cA + z*z*C   ),
        )
        pr = (R[0][0]*p[0] + R[0][1]*p[1] + R[0][2]*p[2],
              R[1][0]*p[0] + R[1][1]*p[1] + R[1][2]*p[2],
              R[2][0]*p[0] + R[2][1]*p[1] + R[2][2]*p[2])
        exps = []
        for v in self.TETRA:
            dx = pr[0]-v[0]; dy = pr[1]-v[1]; dz = pr[2]-v[2]
            exps.append(math.exp(-4.0*(dx*dx+dy*dy+dz*dz)))
        s = sum(exps) or 1.0
        w = [e/s for e in exps]
        offsets = [0.0, 90.0, 180.0, 270.0]
        mix = deg_mean(w, [(self.hue_deg+o)%360.0 for o in offsets])
        return mix

def main():
    ap = argparse.ArgumentParser(description="openWRAITHFRAME-inspired ring renderer")
    ap.add_argument("--fps", type=float, default=48.0)
    ap.add_argument("--width", type=int, default=0)
    ap.add_argument("--margin", type=int, default=1)
    ap.add_argument("--fg", action="store_true", help="use foreground glyph instead of background space")
    ap.add_argument("--glyph", type=str, default="█", help="glyph when using --fg")
    ap.add_argument("--val", type=float, default=0.98)
    ap.add_argument("--sat-min", type=float, default=0.70)
    ap.add_argument("--sat-max", type=float, default=0.95)
    ap.add_argument("--gamma", type=float, default=1.0)
    ap.add_argument("--gate", type=float, default=0.50, help="base gate")
    ap.add_argument("--curve", type=float, default=0.28, help="elliptical curvature")
    ap.add_argument("--gate-noise", type=float, default=0.015)
    ap.add_argument("--attractors", type=int, default=18)
    ap.add_argument("--attr-radius", type=float, default=20.0)
    ap.add_argument("--attr-strength", type=float, default=0.32)
    ap.add_argument("--telic-pressure", type=float, default=0.55)
    ap.add_argument("--glyphs", type=str, default="190,220,260,300,330")
    ap.add_argument("--glyph-strength", type=float, default=0.12)
    ap.add_argument("--segments", type=int, default=32)
    ap.add_argument("--invert", type=float, default=0.35, help="beacon inversion strength")
    ap.add_argument("--rotors", type=int, default=5)
    ap.add_argument("--rotor-speed", type=float, default=0.6)
    ap.add_argument("--rotor-steps", type=int, nargs=2, default=[90, 220])
    ap.add_argument("--rotor-dx", type=float, nargs="+", default=[-2.0,-1.0,-0.5,0.5,1.0,2.0])
    ap.add_argument("--scroll", type=float, default=0.36)
    ap.add_argument("--diff", type=float, default=0.18)
    ap.add_argument("--duration", type=float, default=0.0)
    args = ap.parse_args()

    W = args.width if args.width>0 else term_width(args.margin)
    use_bg = not args.fg
    glyph = args.glyph[0] if args.glyph else "█"

    hues = [random.random()*0.3 + 0.5 for _ in range(W)]
    sats = [random.uniform(args.sat_min, args.sat_max) for _ in range(W)]
    vals = [args.val for _ in range(W)]
    mask = [random.random() for _ in range(W)]

    telic = []
    for _ in range(args.attractors):
        pos = random.uniform(0, W)
        hue_deg = (random.choice([190,210,230,260,280,300,320]) + random.uniform(-10,10)) % 360.0
        telic.append([pos, hue_deg, args.attr_strength, args.attr_radius])

    glyph_hues = [float(x)%360.0 for x in args.glyphs.split(",") if x.strip()]
    glyph_force = args.glyph_strength

    rotors = []
    for _ in range(args.rotors):
        x = random.uniform(0, W)
        dx = random.choice(args.rotor_dx)
        life = random.randint(*args.rotor_steps)
        hue_deg = random.choice(glyph_hues) if glyph_hues else random.uniform(0,360)
        rotors.append(RotorCube(x, dx, life, sigma=8.0, hue_deg=hue_deg, ang_speed=args.rotor_speed))

    dt = 1.0 / max(1.0, args.fps)
    start = time.perf_counter()
    phase = 0.0

    seed_gate = args.gate
    seed_phase = 0.0

    try:
        while True:
            if args.duration>0 and (time.perf_counter()-start) >= args.duration:
                break

            phase = (phase + args.scroll) % W

            # Telic drift
            bins = 24
            if bins>0:
                step = max(1, W//bins)
                mean_h = sum(hues[::step])/max(1, len(hues[::step]))
            else:
                mean_h = sum(hues)/len(hues)
            for a in telic:
                a[1] = (circ_lerp_deg(a[1], (mean_h*360.0)%360.0, 0.01*args.telic_pressure) + 360.0) % 360.0
                a[1] = (circ_lerp_deg(a[1], (a[1]+180.0)%360.0, 0.002) + 360.0) % 360.0
                a[0] = (a[0] + random.uniform(-0.25,0.25)) % W

            # Diffusion
            new_h = [0.0]*W; new_s=[0.0]*W; new_v=[0.0]*W
            for i in range(W):
                L = hues[(i-1) % W]; C = hues[i]; Rr = hues[(i+1) % W]
                dL = L*360.0; dC = C*360.0; dR = Rr*360.0
                m = deg_mean([0.25,0.5,0.25],[dL,dC,dR])/360.0
                h = (1-args.diff)*C + args.diff*m
                grad = abs(((Rr - L + 1.0) % 1.0) - 0.5)*2.0
                s = clamp01(sats[i] + 0.15*(grad-0.5))
                new_h[i]=h; new_s[i]=s; new_v[i]=vals[i]
            hues, sats, vals = new_h, new_s, new_v

            # Rotors
            alive = []
            for rc in rotors:
                if not rc.alive(): continue
                center = rc.x; sigma = rc.sigma; rc_h = rc.hue_field()
                span = int(3*sigma)+1
                for dj in range(-span, span+1):
                    j = int((center + dj) % W)
                    w = gaussian(j, center, sigma)
                    dH = hues[j]*360.0
                    hues[j] = circ_lerp_deg(dH, rc_h, 0.35*w)/360.0
                    sats[j] = clamp01(max(sats[j], args.sat_min + 0.2*w))
                    mask[j] = min(1.0, mask[j] + 0.25*w)
                rc.step(W)
                if rc.alive(): alive.append(rc)
            rotors = alive
            if len(rotors) < args.rotors and random.random() < 0.08:
                x = random.uniform(0, W); dx = random.choice(args.rotor_dx)
                life = random.randint(*args.rotor_steps)
                hue_deg = random.choice(glyph_hues) if glyph_hues else random.uniform(0,360)
                rotors.append(RotorCube(x, dx, life, sigma=8.0, hue_deg=hue_deg, ang_speed=args.rotor_speed))

            # Telic & glyph pulls
            for i in range(W):
                for (pos, hdeg, strength, radius) in telic:
                    dx = min((i - pos) % W, (pos - i) % W)
                    if dx < radius:
                        k = (1.0 - dx/radius)*strength
                        dH = hues[i]*360.0
                        hues[i] = circ_lerp_deg(dH, hdeg, k)/360.0
                if glyph_hues:
                    dH = hues[i]*360.0
                    anchor = min(glyph_hues, key=lambda gh: abs(((gh - dH + 540)%360)-180))
                    hues[i] = circ_lerp_deg(dH, anchor, glyph_force*0.15)/360.0

            # Vacuum mask transport
            new_mask = [0.0]*W
            for i,m in enumerate(mask):
                L = mask[(i-1)%W]; Rr = mask[(i+1)%W]
                new_mask[i] = clamp01(m*0.96 + 0.02*(L+Rr) + random.uniform(-args.gate_noise, args.gate_noise))
            mask = new_mask

            # Beacon inversion on tentative row
            rgb_row = []
            for i in range(W):
                x = (i - (W-1)/2.0)/max(1.0, W-1)
                gate_here = seed_gate + args.curve*(x*x)
                show = mask[i] > gate_here
                h,s,v = hues[i], sats[i], vals[i]
                r,g,b = hsv_to_rgb(h, s, v if show else 0.0)
                rgb_row.append((r,g,b))
            bits = sha_bits(rgb_row, segments=args.segments)
            seg_len = max(1, W // len(bits))
            mismatch = 0
            for si,bit in enumerate(bits):
                a = si*seg_len; b = W if si==len(bits)-1 else (si+1)*seg_len
                bright = sum(1 for j in range(a,b) if (0.2126*rgb_row[j][0]+0.7152*rgb_row[j][1]+0.0722*rgb_row[j][2]) > 128)
                parity = bright % 2
                mismatch += 1 if parity != bit else 0
            err = mismatch / max(1,len(bits))
            seed_gate = clamp01(seed_gate + (0.5-err)*0.02*args.invert)
            seed_phase = (seed_phase + (err-0.5)*args.invert*2.0) % W

            # Render
            out = []
            if use_bg:
                last = None
                for i in range(W):
                    h = (hues[i] + (seed_phase/W)*0.05) % 1.0
                    x = (i - (W-1)/2.0)/max(1.0, W-1)
                    gate_here = seed_gate + args.curve*(x*x)
                    if mask[i] > gate_here:
                        r,g,b = hsv_to_rgb(h, sats[i], vals[i])
                        if last != (r,g,b): out.append(rgb_bg(r,g,b)); last=(r,g,b)
                        out.append(" ")
                    else:
                        if last != (0,0,0): out.append(rgb_bg(0,0,0)); last=(0,0,0)
                        out.append(" ")
                out.append(RESET)
            else:
                for i in range(W):
                    h = (hues[i] + (seed_phase/W)*0.05) % 1.0
                    r,g,b = hsv_to_rgb(h, sats[i], vals[i])
                    out.append(rgb_fg(r,g,b) + glyph)
                out.append(RESET)
            sys.stdout.write("".join(out) + "\n")
            sys.stdout.flush()

            time.sleep(dt)

    except KeyboardInterrupt:
        print(RESET, end="")

if __name__ == "__main__":
    main()
