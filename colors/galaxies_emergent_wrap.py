
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
galaxies_emergent_wrap.py
Dusty-style terminal color-automata with:
 - ring topology (wrap-around neighbors)
 - background-color printing by default using a space glyph
 - moving flow field to bias diagonals
 - many attractors (some seeded, some emergent from gradient maxima)
 - anti-convergence "entropy" kicks when palette collapses
 - minimal deps (stdlib only)

Run:
  python3 galaxies_emergent_wrap.py
Stop with Ctrl-C.

CLI knobs are optional; sensible defaults are chosen for iOS terminals.
"""

import sys, os, time, math, random, shutil, argparse

# ---------- ANSI helpers ----------

RESET = "\x1b[0m"

def bg_rgb(r, g, b):
    # Clamp for safety
    r = max(0, min(255, int(r)))
    g = max(0, min(255, int(g)))
    b = max(0, min(255, int(b)))
    return f"\x1b[48;2;{r};{g};{b}m"

def fg_rgb(r, g, b):
    r = max(0, min(255, int(r)))
    g = max(0, min(255, int(g)))
    b = max(0, min(255, int(b)))
    return f"\x1b[38;2;{r};{g};{b}m"

# ---------- Color math (HSV with circular hue) ----------

def hsv_to_rgb(h, s, v):
    """h in [0,1), s in [0,1], v in [0,1]"""
    h = (h % 1.0) * 6.0
    i = int(h)
    f = h - i
    p = v * (1.0 - s)
    q = v * (1.0 - s * f)
    t = v * (1.0 - s * (1.0 - f))
    if i == 0: r, g, b = v, t, p
    elif i == 1: r, g, b = q, v, p
    elif i == 2: r, g, b = p, v, t
    elif i == 3: r, g, b = p, q, v
    elif i == 4: r, g, b = t, p, v
    else: r, g, b = v, p, q
    return int(r * 255), int(g * 255), int(b * 255)

def circ_mean(angles):
    """Circular mean of hues in [0,1)"""
    sx = 0.0
    sy = 0.0
    for a in angles:
        ang = a * 2.0 * math.pi
        sx += math.cos(ang)
        sy += math.sin(ang)
    if sx == 0 and sy == 0:
        return angles[0]
    ang = math.atan2(sy, sx) / (2.0 * math.pi)
    if ang < 0: ang += 1.0
    return ang

def lerp_angle(a, b, t):
    """Shortest-path interpolation between hues a,b in [0,1), factor t in [0,1]."""
    # Convert to radians
    A = a * 2.0 * math.pi
    B = b * 2.0 * math.pi
    # Wrap diff into [-pi, pi]
    d = (B - A + math.pi) % (2.0 * math.pi) - math.pi
    C = A + d * t
    C = (C + 2.0 * math.pi) % (2.0 * math.pi)
    out = C / (2.0 * math.pi)
    return out

def hue_dist(a, b):
    """Distance on hue circle in [0, 0.5]"""
    d = abs((a - b + 0.5) % 1.0 - 0.5)
    return d

# ---------- Flow field (smooth random) ----------

class SmoothNoise1D:
    """Simple filtered random walk to avoid dependency on noise libs."""
    def __init__(self, n, jitter=0.02):
        self.n = n
        self.v = [random.uniform(-1,1) for _ in range(n)]
        self.jitter = jitter

    def step(self, damp=0.95):
        for i in range(self.n):
            self.v[i] = damp * self.v[i] + (1.0 - damp) * random.uniform(-1, 1)
        return self.v

# ---------- Attractors ----------

class Attractor:
    __slots__ = ("pos","hue","strength","radius","vx","life","id")
    _next_id = 1
    def __init__(self, pos, hue, strength, radius, vx=0.0, life=120):
        self.pos = pos
        self.hue = hue % 1.0
        self.strength = strength
        self.radius = radius
        self.vx = vx
        self.life = life
        self.id = Attractor._next_id
        Attractor._next_id += 1

    def tick(self, width):
        self.pos = (self.pos + self.vx) % width
        self.life -= 1
        return self.life > 0

# ---------- Engine ----------

def build_parser():
    p = argparse.ArgumentParser(description="Emergent ring CA with attractors & anti-convergence")
    p.add_argument("--width", type=int, default=0, help="override terminal width")
    p.add_argument("--rows", type=int, default=0, help="rows to draw (0=until Ctrl-C)")
    p.add_argument("--fps", type=float, default=18.0, help="target frames per second")

    # Rendering
    p.add_argument("--fg", action="store_true", help="use foreground blocks instead of background spaces")
    p.add_argument("--glyph", type=str, default="█", help="glyph when --fg (default: █)")
    p.add_argument("--space-glyph", type=str, default=" ", help="glyph when using background (default: space)")

    # Palette shaping
    p.add_argument("--sat-min", type=float, default=0.65, help="minimum saturation floor")
    p.add_argument("--sat-boost", type=float, default=0.08, help="boost near gradients/attractors")
    p.add_argument("--val", type=float, default=0.95, help="value/brightness")
    p.add_argument("--contrast", type=float, default=1.25, help="contrast shaping on saturation")
    p.add_argument("--gamma", type=float, default=1.0, help="gamma on V")

    # Diffusion / advection
    p.add_argument("--diff", type=float, default=0.15, help="blend towards neighbor circular mean")
    p.add_argument("--flow-speed", type=float, default=1.0, help="pixels of advection per frame at flow=1.0")
    p.add_argument("--flows", type=int, default=6, help="number of flow streams")
    p.add_argument("--flow-width", type=float, default=18.0, help="stddev of gaussian stream width")
    p.add_argument("--flow-drift", type=float, default=0.22, help="random drift of stream centers per frame [0..1]")

    # Attractors
    p.add_argument("--attractors", type=int, default=14, help="seeded attractors")
    p.add_argument("--attr-strength", type=float, default=0.35, help="base strength")
    p.add_argument("--attr-radius", type=float, default=22.0, help="influence radius (pixels)")
    p.add_argument("--attr-life", type=int, default=240, help="life in frames for seeded attractors")
    p.add_argument("--emerge-thresh", type=float, default=0.12, help="gradient threshold to spawn emergent attractors")
    p.add_argument("--emerge-cool", type=int, default=12, help="cooldown (frames) before same site can spawn again")

    # Anti-convergence
    p.add_argument("--entropy-var", type=float, default=0.020, help="if hue variance below this, kick entropy")
    p.add_argument("--entropy-kick", type=float, default=0.35, help="kick strength for entropy attractors")
    p.add_argument("--entropy-count", type=int, default=3, help="how many entropy attractors per kick")
    p.add_argument("--entropy-life", type=int, default=140, help="life of entropy attractors")

    # Glider/spark seeding (gentle)
    p.add_argument("--spawn", type=float, default=0.03, help="probability per frame to spawn a hue glider")
    p.add_argument("--g-life", type=int, nargs=2, default=[60, 140], help="min max glider life")
    p.add_argument("--seg-len", type=int, nargs=2, default=[14, 36], help="min max segment length before heading change")
    p.add_argument("--segments", type=int, nargs=2, default=[3, 6], help="min max segments in a flight plan")
    p.add_argument("--dx", type=float, nargs="+", default=[-2,-1,-0.5,0.5,1,2], help="candidate dx choices for gliders")

    return p

def gaussian(x, mu, sigma):
    return math.exp(-0.5 * ((x - mu) / sigma) ** 2)

def build_streams(width, count, sigma, drift):
    streams = []
    for _ in range(count):
        cx = random.uniform(0, width)
        sgn = random.choice([-1.0, 1.0])
        speed = sgn  # base signed unit; scaled by --flow-speed later
        streams.append([cx, speed, random.uniform(0.6,1.0), sigma, drift])
    return streams

def flow_field(width, streams, flow_speed):
    field = [0.0]*width
    for cx, speed, amp, sigma, drift in streams:
        # contribute gaussian velocity profile
        for i in range(width):
            g = gaussian(i, cx, sigma)
            field[i] += amp * speed * g * flow_speed
    return field

def drift_streams(width, streams, flow_drift):
    for s in streams:
        s[0] = (s[0] + random.uniform(-flow_drift, flow_drift)) % width

class Glider:
    def __init__(self, pos, hue, plan, life):
        self.pos = pos
        self.hue = hue % 1.0
        self.plan = plan[:]  # list of (dx, steps)
        self.left = self.plan.pop(0) if self.plan else (0.0, 9999)
        self.dx, self.steps = self.left
        self.life = life

    def step(self, width):
        # advance pos
        self.pos = (self.pos + self.dx) % width
        self.steps -= 1
        self.life -= 1
        if self.steps <= 0 and self.plan:
            self.dx, self.steps = self.plan.pop(0)
        return self.life > 0

def circular_variance(hues):
    # Var on unit circle: 1 - R where R is mean resultant length
    sx = sy = 0.0
    for h in hues:
        ang = h * 2.0 * math.pi
        sx += math.cos(ang)
        sy += math.sin(ang)
    R = math.hypot(sx, sy) / max(1, len(hues))
    return 1.0 - R

def main():
    args = build_parser().parse_args()

    # Terminal geometry
    if args.width > 0:
        W = args.width
    else:
        W = shutil.get_terminal_size((80, 24)).columns
        W = max(40, min(240, W))

    # Render mode defaults: background space unless --fg
    use_fg = args.fg
    glyph = args.glyph if use_fg else args.space_glyph

    # Initialize colors (HSV)
    hues = [random.random() for _ in range(W)]
    sats = [random.uniform(args.sat_min, 1.0) for _ in range(W)]
    vals = [args.val for _ in range(W)]

    # Streams and noise
    streams = build_streams(W, args.flows, args.flow_width, args.flow_drift)
    noise = SmoothNoise1D(W, jitter=0.02)

    # Attractors
    attractors = []
    def seed_attractor(pos=None, hue=None, strength=None, radius=None, life=None, drift=True):
        p = random.uniform(0, W) if pos is None else pos
        h = random.random() if hue is None else hue
        s = args.attr_strength if strength is None else strength
        r = args.attr_radius if radius is None else radius
        vx = random.uniform(-0.15, 0.15) if drift else 0.0
        L = args.attr_life if life is None else life
        attractors.append(Attractor(p, h, s, r, vx=vx, life=L))

    for _ in range(args.attractors):
        # Seed around triads/compliments to start with a wide wheel spread
        base = random.random()
        for off in (0.0, 1/3, 2/3):
            if random.random() < 0.5:
                seed_attractor(hue=(base+off)%1.0)

    # Emergent spawn memory (cooldown per site)
    cooldown = [0]*W

    gliders = []

    # Timing
    dt = 1.0 / max(1e-6, args.fps)
    t0 = time.perf_counter()

    row_limit = args.rows if args.rows > 0 else None
    row_count = 0

    try:
        while True:
            # Flow field + drift
            drift_streams(W, streams, args.flow_drift)
            flow = flow_field(W, streams, args.flow_speed)
            noise.step()

            # Advection step (diagonals): pull color from shifted source index
            adv_hues = [0.0]*W
            adv_sats = [0.0]*W
            adv_vals = [0.0]*W
            for i in range(W):
                src = int((i - flow[i])) % W
                adv_hues[i] = hues[src]
                adv_sats[i] = sats[src]
                adv_vals[i] = vals[src]

            # Diffusion (neighbor circular mean)
            new_hues = [0.0]*W
            new_sats = [0.0]*W
            new_vals = [0.0]*W

            for i in range(W):
                L = adv_hues[(i-1) % W]
                C = adv_hues[i]
                R = adv_hues[(i+1) % W]
                hmean = circ_mean([L, C, R])
                h = lerp_angle(C, hmean, args.diff)

                # Attractor pulls (multi-source, distance falloff)
                for a in attractors:
                    # ring distance shortest way
                    dx = min((i - a.pos) % W, (a.pos - i) % W)
                    if dx < a.radius:
                        k = (1.0 - dx / a.radius) * a.strength
                        h = lerp_angle(h, a.hue, k)

                # Gentle noise to avoid gridlock
                n = noise.v[i] * 0.002
                h = (h + n) % 1.0

                new_hues[i] = h

                # Saturation shaping
                grad = hue_dist(L, R)
                s = max(args.sat_min, adv_sats[i] + args.sat_boost * grad)
                s = max(0.0, min(1.0, s))
                # Contrast shaping on saturation
                s = max(0.0, min(1.0, (s - 0.5) * args.contrast + 0.5))
                new_sats[i] = s

                v = max(0.0, min(1.0, adv_vals[i]))
                if args.gamma != 1.0:
                    v = v ** args.gamma
                new_vals[i] = v

            hues, sats, vals = new_hues, new_sats, new_vals

            # Emergent attractors from gradient maxima
            for i in range(W):
                if cooldown[i] > 0:
                    cooldown[i] -= 1
                    continue
                g = hue_dist(hues[(i-1)%W], hues[(i+1)%W])
                if g > args.emerge_thresh:
                    # Spawn with either local hue or its complement for competition
                    if random.random() < 0.5:
                        target = hues[i]
                    else:
                        target = (hues[i] + 0.5) % 1.0
                    seed_attractor(pos=i + random.uniform(-4,4), hue=target,
                                   strength=args.attr_strength*0.8,
                                   radius=args.attr_radius*0.8,
                                   life=int(args.attr_life*0.6))
                    cooldown[i] = args.emerge_cool

            # Anti-convergence entropy
            var = circular_variance(hues)
            if var < args.entropy_var and random.random() < 0.5:
                # Kick with a set of well-separated hues (complement + triads)
                base = random.random()
                hues_to_seed = [(base + 0.0) % 1.0, (base + 0.5) % 1.0, (base + 1/3) % 1.0, (base + 2/3) % 1.0]
                random.shuffle(hues_to_seed)
                for k in range(min(args.entropy_count, len(hues_to_seed))):
                    pos = random.uniform(0, W)
                    seed_attractor(pos=pos, hue=hues_to_seed[k],
                                   strength=args.entropy_kick,
                                   radius=args.attr_radius*1.1,
                                   life=args.entropy_life)

            # Update attractors and gliders
            attractors = [a for a in attractors if a.tick(W)]

            # Occasional glider spawn pulling hue along a diagonal
            if random.random() < args.spawn:
                life = random.randint(args.g_life[0], args.g_life[1])
                segs = random.randint(args.segments[0], args.segments[1])
                plan = []
                for _ in range(segs):
                    dx = random.choice(args.dx)
                    steps = random.randint(args.seg_len[0], args.seg_len[1])
                    plan.append((dx, steps))
                g = Glider(pos=random.uniform(0, W),
                           hue=random.random(),
                           plan=plan,
                           life=life)
                gliders.append(g)

            # Apply gliders as localized hue pulls & add slight trail
            keep = []
            for g in gliders:
                if g.step(W):
                    keep.append(g)
                    i = int(g.pos) % W
                    # Pull neighbors toward glider hue with gaussian falloff
                    for off in range(-6, 7):
                        j = (i + off) % W
                        k = gaussian(j, i, 3.5) * 0.35
                        hues[j] = lerp_angle(hues[j], g.hue, k)
                        sats[j] = max(sats[j], args.sat_min + 0.15*k)
                # else dropped
            gliders = keep

            # Draw one row
            pieces = []
            if use_fg:
                # Foreground glyph colored; leave background default
                for i in range(W):
                    r,g,b = hsv_to_rgb(hues[i], sats[i], vals[i])
                    pieces.append(f"{fg_rgb(r,g,b)}{glyph}")
            else:
                for i in range(W):
                    r,g,b = hsv_to_rgb(hues[i], sats[i], vals[i])
                    pieces.append(f"{bg_rgb(r,g,b)}{args.space_glyph}")
            line = "".join(pieces) + RESET
            print(line)
            sys.stdout.flush()

            row_count += 1
            if row_limit is not None and row_count >= row_limit:
                break

            # frame pacing
            t0 += dt
            sleep_for = t0 - time.perf_counter()
            if sleep_for > 0:
                time.sleep(sleep_for)
            else:
                t0 = time.perf_counter()
    except KeyboardInterrupt:
        print(RESET, end="")

if __name__ == "__main__":
    main()
