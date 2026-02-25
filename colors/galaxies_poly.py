
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
galaxies_poly.py
A 1-D ring color automaton driven by a rotating tetrahedron in 3D color space.
Stdlib only.
"""
import sys, math, time, shutil, argparse, random

ESC = "\x1b["
RESET = "\x1b[0m"

def term_width(margin:int=1) -> int:
    cols = shutil.get_terminal_size().columns
    return max(10, cols - margin)

def clamp(x, lo, hi):
    return lo if x < lo else hi if x > hi else x

def hsv_to_rgb(h, s, v):
    if s <= 0.0:
        r = g = b = int(255*v)
        return r,g,b
    i = int(h*6.0)
    f = h*6.0 - i
    p = v*(1.0 - s)
    q = v*(1.0 - s*f)
    t = v*(1.0 - s*(1.0 - f))
    i = i % 6
    if i == 0: r,g,b = v,t,p
    elif i == 1: r,g,b = q,v,p
    elif i == 2: r,g,b = p,v,t
    elif i == 3: r,g,b = p,q,v
    elif i == 4: r,g,b = t,p,v
    else: r,g,b = v,p,q
    return int(255*r), int(255*g), int(255*b)

def rgb_bg(r,g,b):
    return f"\x1b[48;2;{r};{g};{b}m"

def rgb_fg(r,g,b):
    return f"\x1b[38;2;{r};{g};{b}m"

def rot_matrix(axis, angle):
    x,y,z = axis
    n = (x*x + y*y + z*z)**0.5
    if n == 0: return [[1,0,0],[0,1,0],[0,0,1]]
    x,y,z = x/n, y/n, z/n
    c = math.cos(angle); s=math.sin(angle); C = 1-c
    return [
        [c + x*x*C,     x*y*C - z*s,  x*z*C + y*s],
        [y*x*C + z*s,   c + y*y*C,    y*z*C - x*s],
        [z*x*C - y*s,   z*y*C + x*s,  c + z*z*C   ],
    ]

def mat_vec(m, v):
    return [
        m[0][0]*v[0] + m[0][1]*v[1] + m[0][2]*v[2],
        m[1][0]*v[0] + m[1][1]*v[1] + m[1][2]*v[2],
        m[2][0]*v[0] + m[2][1]*v[1] + m[2][2]*v[2],
    ]

def softmax_neg_sq_dists(point, verts, beta):
    exps = []
    for v in verts:
        dx = point[0]-v[0]; dy = point[1]-v[1]; dz = point[2]-v[2]
        exps.append(math.exp(-beta*(dx*dx+dy*dy+dz*dz)))
    s = sum(exps) or 1.0
    return [e/s for e in exps]

def circ_mean_deg(weights, hues_deg):
    sx = 0.0; sy = 0.0
    for w,h in zip(weights, hues_deg):
        rad = math.radians(h)
        sx += w*math.cos(rad); sy += w*math.sin(rad)
    ang = math.atan2(sy, sx)
    deg = (math.degrees(ang) + 360.0) % 360.0
    return deg

def lerp(a,b,t): return a + (b-a)*t

def build_palette(name):
    presets = {
        "aurora": dict(h=[150, 200, 260, 320], s=0.72, v=0.96),
        "glacier": dict(h=[180, 200, 220, 240], s=0.60, v=0.95),
        "abyss": dict(h=[190, 210, 240, 280], s=0.85, v=0.92),
        "moonlit": dict(h=[180, 210, 300, 330], s=0.70, v=0.98),
        "pearl": dict(h=[180, 210, 230, 310], s=0.55, v=0.98),
    }
    return presets.get(name, presets["aurora"])

def main():
    ap = argparse.ArgumentParser(description="1D ring driven by rotating tetrahedron")
    ap.add_argument("--fps", type=float, default=48, help="frames per second")
    ap.add_argument("--width", type=int, default=0, help="manual width; default=auto")
    ap.add_argument("--margin", type=int, default=1, help="columns kept blank to avoid wrap")
    ap.add_argument("--glyph", default=" ", help="single character to render (default space bg)")
    ap.add_argument("--fg", action="store_true", help="use foreground color on glyph (not bg)")
    ap.add_argument("--palette", default="aurora", help="palette preset")
    ap.add_argument("--hues", default="", help="custom vertex hues as comma degrees, e.g. 180,210,250,310")
    ap.add_argument("--sat-min", type=float, default=0.65, help="min saturation")
    ap.add_argument("--sat-max", type=float, default=0.95, help="max saturation")
    ap.add_argument("--val", type=float, default=0.98, help="value/brightness")
    ap.add_argument("--beta", type=float, default=4.0, help="softmin sharpness (higher = crisper bands)")
    ap.add_argument("--tilt", type=float, default=0.25, help="z tilt of sampling circle [-1..1]")
    ap.add_argument("--tilt-drift", type=float, default=0.15, help="slow change of tilt over time")
    ap.add_argument("--axis", default="1,1,0", help="rotation axis x,y,z (normalized internally)")
    ap.add_argument("--speed", type=float, default=0.8, help="rotation speed (rad/frame)")
    ap.add_argument("--scroll", type=float, default=0.35, help="index scroll per frame (diagonal slope)")
    ap.add_argument("--diff", type=float, default=0.15, help="blend with previous frame [0..1]")
    ap.add_argument("--mate-rate", type=float, default=0.002, help="offspring hue rate per frame")
    ap.add_argument("--mate-jitter", type=float, default=6.0, help="offspring hue jitter (degrees)")
    ap.add_argument("--duration", type=float, default=0, help="seconds to run; 0=infinite")
    args = ap.parse_args()

    W = args.width if args.width and args.width>0 else term_width(args.margin)
    glyph = args.glyph[0] if args.glyph else " "
    use_bg = not args.fg

    pal = build_palette(args.palette)
    if args.hues:
        try:
            hh = [float(x) for x in args.hues.split(",")]
            if len(hh) == 4:
                pal["h"] = hh
        except: pass
    hues = pal["h"][:]
    sat_base = clamp(pal.get("s", 0.7), 0.0, 1.0)
    val = clamp(args.val, 0.0, 1.0)
    sat_min = clamp(args.sat_min, 0.0, 1.0)
    sat_max = clamp(args.sat_max, 0.0, 1.0)

    base_verts = [
        ( 1,  1,  1),
        ( 1, -1, -1),
        (-1,  1, -1),
        (-1, -1,  1),
    ]
    base_verts = [tuple([c / (3**0.5) for c in v]) for v in base_verts]

    ax = tuple(float(x) for x in args.axis.split(","))
    angle = 0.0
    phase = 0.0
    prev_rgb = [(0,0,0)]*W

    start = time.time()
    dt = 1.0 / max(1.0, args.fps)

    tilt_phase = random.random()*math.tau

    while True:
        if args.duration>0 and (time.time()-start) >= args.duration:
            break

        angle += args.speed
        R = rot_matrix(ax, angle)
        verts = [mat_vec(R, v) for v in base_verts]

        tilt_phase += args.tilt_drift*0.01
        ztilt = clamp(args.tilt + 0.25*math.sin(tilt_phase), -1.0, 1.0)

        if random.random() < args.mate_rate:
            a,b,c = random.sample(range(4), 3)
            def circ_blend(h1,h2,t):
                r1 = math.radians(h1); r2 = math.radians(h2)
                x = math.cos(r1)*(1-t) + math.cos(r2)*t
                y = math.sin(r1)*(1-t) + math.sin(r2)*t
                ang = (math.degrees(math.atan2(y,x))+360)%360
                return (ang + random.uniform(-args.mate_jitter, args.mate_jitter))%360
            hues[c] = circ_blend(hues[a], hues[b], 0.5)

        colors_rgb = [None]*W
        phase = (phase + args.scroll) % W
        hue_deg = hues

        for i in range(W):
            t = (i + phase) / W
            theta = t * math.tau
            p = (math.cos(theta), math.sin(theta), ztilt)
            w = softmax_neg_sq_dists(p, verts, args.beta)

            conf = max(w)
            s = clamp(lerp(sat_min, sat_max, conf*0.9 + 0.1), 0.0, 1.0)

            h_deg = circ_mean_deg(w, hue_deg)
            h = (h_deg % 360.0) / 360.0

            r,g,b = hsv_to_rgb(h, s, val)
            pr,pg,pb = prev_rgb[i]
            mix = clamp(args.diff, 0.0, 1.0)
            r = int(pr*(mix) + r*(1-mix)); g = int(pg*(mix) + g*(1-mix)); b = int(pb*(mix) + b*(1-mix))
            colors_rgb[i] = (r,g,b)

        prev_rgb = colors_rgb

        out = []
        if use_bg:
            last = None
            for (r,g,b) in colors_rgb:
                if last != (r,g,b):
                    out.append(rgb_bg(r,g,b))
                    last = (r,g,b)
                out.append(glyph)
            out.append(RESET)
        else:
            for (r,g,b) in colors_rgb:
                out.append(rgb_fg(r,g,b) + glyph)
            out.append(RESET)
        sys.stdout.write("".join(out) + "\n")
        sys.stdout.flush()

        if dt > 0:
            time.sleep(dt)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(RESET, end="")
