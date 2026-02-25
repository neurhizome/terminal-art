#!/usr/bin/env python3
# Dusty's Orchestrated Galaxies — v6
# - wrap-around neighbors (circular row)
# - persistent diagonal "streams" that advect color horizontally
# - gliders with preplanned multi-segment trajectories
# - command-line knobs for everything, still zero extra deps

import sys, time, shutil, random as R, math, argparse

def term_width():
    try: return max(40, shutil.get_terminal_size().columns - 2)
    except: return 120

def clamp(x, lo=0, hi=255):
    return lo if x < lo else hi if x > hi else x

def luma(v):
    r,g,b=v; return 0.2126*r + 0.7152*g + 0.0722*b

def paint(rgb, ch, use_bg=False):
    r,g,b = (int(clamp(c)) for c in rgb)
    return (f"\x1b[48;2;{r};{g};{b}m{ch}\x1b[0m" if use_bg
            else f"\x1b[38;2;{r};{g};{b}m{ch}\x1b[0m")

def posterize(rgb, levels):
    if levels <= 1: return [int(c) for c in rgb]
    step = 255.0/(levels-1)
    return [int(round(c/step)*step) for c in rgb]

def lerp(a,b,t): return a*(1-t)+b*t
def rgb_lerp(a,b,t): return [lerp(a[0],b[0],t), lerp(a[1],b[1],t), lerp(a[2],b[2],t)]
def rgb_dist(a,b): return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2) + 1e-6

def softmax_temp(z, temp):
    z = [v/max(1e-9,temp) for v in z]
    m = max(z); ez = [math.exp(v-m) for v in z]; s = sum(ez)
    return [e/s for e in ez]

def line_brightness_adjust(row, target, gain):
    mean = sum(luma(v) for v in row) / len(row)
    k = 1.0 + gain * (target - mean) / 255.0
    return [[clamp(c*k) for c in v] for v in row]

def apply_contrast_and_saturation(row, contrast, sat_boost, chroma_floor, gamma):
    # per-channel mean for contrast
    chmeans = [sum(v[i] for v in row)/len(row) for i in range(3)]
    out = []
    for v in row:
        vv = [chmeans[i] + (v[i]-chmeans[i])*contrast for i in range(3)]
        L = luma(vv)
        dv = [vv[0]-L, vv[1]-L, vv[2]-L]
        vv = [L + d*sat_boost for d in dv]
        mag = math.sqrt(dv[0]**2 + dv[1]**2 + dv[2]**2)
        if mag < chroma_floor and mag > 1e-6:
            s = chroma_floor / mag
            vv = [L + (vv[0]-L)*s, L + (vv[1]-L)*s, L + (vv[2]-L)*s]
        vv = [255.0*((clamp(c)/255.0)**gamma) for c in vv]
        out.append([clamp(c) for c in vv])
    return out

def wrap_idx(i, W): 
    # python's % already wraps negative to positive modulus
    return i % W

def sample_rgb(arr, x):
    """Fractional wrap-around sample at position x (columns)."""
    W = len(arr)
    i0 = int(math.floor(x)) % W
    i1 = (i0 + 1) % W
    t = x - math.floor(x)
    return [lerp(arr[i0][k], arr[i1][k], t) for k in range(3)]

# ------------- Streams (persistent diagonal advection) -------------
class Stream:
    __slots__ = ("x","w","v","life","age","drift")
    def __init__(self, x, w, v, life, drift):
        self.x=float(x); self.w=float(w); self.v=float(v); self.life=int(life); self.age=0
        self.drift=float(drift)  # lateral drift of the stream center per row
    def alive(self): return self.age < self.life
    def step(self, W):
        self.x = (self.x + self.drift) % W
        self.age += 1
    def vel_at(self, j):
        d = (j - self.x) / max(1e-6, self.w)
        return self.v * math.exp(-0.5*d*d)

# ------------- Gliders (with scheduled direction segments) -------------
class Glider:
    __slots__ = ("x","life","age","w","col","col2","sched","seg_i","seg_t","alpha_peak","fade_frac")
    def __init__(self, x, life, w, col, col2, schedule, alpha_peak, fade_frac):
        self.x=float(x); self.life=int(life); self.age=0; self.w=float(w)
        self.col=col; self.col2=col2; self.sched=schedule; self.seg_i=0; self.seg_t=0
        self.alpha_peak = alpha_peak; self.fade_frac=fade_frac
    def alive(self): return self.age < self.life
    def current_dx(self):
        if self.seg_i >= len(self.sched): return 0.0
        dx, dur = self.sched[self.seg_i]
        return dx
    def step(self, W):
        if self.seg_i < len(self.sched):
            dx, dur = self.sched[self.seg_i]
            self.x = (self.x + dx) % W
            self.seg_t += 1
            if self.seg_t >= dur:
                self.seg_i += 1
                self.seg_t = 0
        self.age += 1
    def alpha(self):
        t = self.age / max(1, self.life-1)
        f = self.fade_frac
        if t < f: a = t/f
        elif t > 1-f: a = (1-t)/f
        else: a = 1.0
        return self.alpha_peak * max(0.0, min(1.0, a))
    def color_now(self, sat_boost):
        t = self.age / max(1, self.life-1)
        base = rgb_lerp(self.col, self.col2, 0.5*t)
        L = luma(base); dv = [base[0]-L, base[1]-L, base[2]-L]
        return [L + d*sat_boost for d in dv]

# ------------- Engine -------------
def main():
    p = argparse.ArgumentParser(description="Dusty's Orchestrated Galaxies — wrap-around + streams")
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--glyph", type=str, default="█")
    p.add_argument("--bg", action="store_true", help="use background color instead of foreground")
    p.add_argument("--width", type=int, default=0, help="override terminal width")
    # diffusion + mask
    p.add_argument("--posterize", type=int, default=20)
    p.add_argument("--target-luma", type=float, default=112)
    p.add_argument("--gain", type=float, default=0.02)
    p.add_argument("--gate", type=float, default=0.52)
    p.add_argument("--curve", type=float, default=0.28)
    # contrast/sat
    p.add_argument("--contrast", type=float, default=1.25)
    p.add_argument("--sat", type=float, default=1.35)
    p.add_argument("--chroma", type=float, default=26.0)
    p.add_argument("--gamma", type=float, default=0.95)
    # attractors
    p.add_argument("--temp", type=float, default=0.65)
    p.add_argument("--pressure", type=float, default=0.52)
    p.add_argument("--mutate", type=float, default=0.025)
    # streams
    p.add_argument("--flows", type=int, default=5)
    p.add_argument("--flow-speed", type=float, default=1.0, help="max column shift per row for a stream")
    p.add_argument("--flow-width", type=float, default=14.0)
    p.add_argument("--flow-life", type=int, nargs=2, default=[120, 380])
    p.add_argument("--flow-drift", type=float, default=0.25, help="lateral drift of stream center per row")
    p.add_argument("--flow-spawn", type=float, default=0.08)
    # gliders
    p.add_argument("--spawn", type=float, default=0.05)
    p.add_argument("--g-life", type=int, nargs=2, default=[35, 120])
    p.add_argument("--g-width", type=float, nargs=2, default=[4.0, 18.0])
    p.add_argument("--alpha-peak", type=float, default=0.6)
    p.add_argument("--fade-frac", type=float, default=0.25)
    p.add_argument("--dx", type=float, nargs="+", default=[-2,-1,-0.5,0.5,1,2])
    p.add_argument("--segments", type=int, nargs=2, default=[2, 5], help="min/max glider schedule segments")
    p.add_argument("--seg-len", type=int, nargs=2, default=[8, 40], help="min/max frames per segment")
    args = p.parse_args()

    # attractors spaced around a vivid wheel
    ATTR = [
        (242, 63, 58),
        (53, 220, 59),
        (63, 110, 255),
        (250, 210, 55),
        (198, 63, 241),
        (55, 238, 240),
    ]

    W = args.width if args.width > 0 else term_width()
    rgb = [[R.randint(0,255) for _ in range(3)] for _ in range(W)]
    ms  = [R.random() for _ in range(W)]

    weights = [1/len(ATTR)] * len(ATTR)
    gliders = []
    streams = []

    def maybe_spawn_stream():
        if len(streams) >= args.flows: return
        if R.random() > args.flow_spawn: return
        x = R.uniform(0, W)
        w = max(2.0, R.gauss(args.flow_width, args.flow_width*0.15))
        v = R.uniform(-args.flow_speed, args.flow_speed)
        life = R.randint(*args.flow_life)
        drift = R.uniform(-args.flow_drift, args.flow_drift)
        streams.append(Stream(x, w, v, life, drift))

    def velocity_field():
        u = [0.0]*W
        alive = []
        for s in streams:
            if not s.alive(): continue
            # sample within 3*sigma
            left = int(max(0, math.floor(s.x - 3*s.w)))
            right = int(min(W-1, math.ceil(s.x + 3*s.w)))
            if right < left:
                left, right = 0, W-1
            for j in range(left, right+1):
                # wrap distance by considering two images shifted by W
                d0 = (j - s.x)
                d1 = d0 - W
                d2 = d0 + W
                d = min(abs(d0), abs(d1), abs(d2)) / max(1e-6, s.w)
                if d <= 3.5:
                    u[j] += s.v * math.exp(-0.5*d*d)
            s.step(W)
            if s.alive(): alive.append(s)
        streams[:] = alive
        return u

    def advect_row(row, u):
        out = [None]*W
        for i in range(W):
            # positive u moves color to the right -> sample from left
            src = i - u[i]
            out[i] = sample_rgb(row, src)
        return out

    def spawn_glider():
        # choose start near a mask edge for visibility half the time
        if R.random() < 0.5:
            edge = [i for i,v in enumerate(ms) if abs(v-args.gate) < 0.03]
            x = float(R.choice(edge)) if edge else float(R.randint(0,W-1))
        else:
            x = float(R.randint(0, W-1))
        life = R.randint(*args.g_life)
        w    = R.uniform(*args.g_width)
        # choose a schedule: N segments, each with dx from args.dx and length in seg-len
        nseg = R.randint(*args.segments)
        sched = [(R.choice(args.dx), R.randint(*args.seg_len)) for _ in range(nseg)]
        ahead = int((x + 2*sum(dx for dx,_ in sched)) % W)
        local = rgb[ahead][:]
        # pick attractor by current weights
        r = R.random(); s=0.0; k=0
        for i,wgt in enumerate(weights):
            s+=wgt
            if r<=s: k=i; break
        toward = ATTR[k]
        gliders.append(Glider(x, life, w, local, toward, sched, args.alpha_peak, args.fade_frac))

    def mask_gate(val, x):
        return args.gate + args.curve * (x*x)

    sys.stdout.write("\x1b[?25l")
    try:
        while True:
            # 1) attractor fitness from current row
            fit = []
            for a in ATTR:
                s = 0.0
                for v in rgb[::max(1, W//120)]:
                    s += 1.0 / rgb_dist(v, a)
                fit.append(s)
            fit = softmax_temp(fit, args.temp)
            mutated = [(w + R.uniform(-args.mutate, args.mutate)) for w in weights]
            mutated = [max(1e-6, m) for m in mutated]
            sm = sum(mutated); mutated = [m/sm for m in mutated]
            weights = [lerp(mutated[i], fit[i], args.pressure) for i in range(len(ATTR))]
            sw = sum(weights); weights = [w/sw for w in weights]

            # 2) maybe spawn streams + get velocity field
            maybe_spawn_stream()
            u = velocity_field()

            # 3) maybe spawn a glider
            if R.random() < args.spawn:
                spawn_glider()

            # 4) base diffusion (wrap neighbors)
            new_rgb = [None]*W
            for i, me in enumerate(rgb):
                Lc = rgb[(i-1) % W]
                Rc = rgb[(i+1) % W]
                # bias slightly across screen to encourage asymmetry
                x = (i - (W-1)/2.0) / max(1.0, W-1)
                wl = 0.52 + 0.02*x
                wr = 0.52 - 0.02*x
                w0 = 1.0
                div = 2.0
                new_rgb[i] = [
                    (w0*me[0] + wl*Lc[0] + wr*Rc[0]) / div,
                    (w0*me[1] + wl*Lc[1] + wr*Rc[1]) / div,
                    (w0*me[2] + wl*Lc[2] + wr*Rc[2]) / div,
                ]

            # 5) advection by streams (creates diagonal expansion)
            new_rgb = advect_row(new_rgb, u)

            # 6) posterize + line brightness
            new_rgb = [posterize(v, args.posterize) for v in new_rgb]
            new_rgb = line_brightness_adjust(new_rgb, args.target_luma, args.gain)

            # 7) update mask with a gentle wrap-around diffusion too
            new_ms = [None]*W
            for i, m in enumerate(ms):
                Lm = ms[(i-1) % W]; Rm = ms[(i+1) % W]
                mbias = 0.01 + 0.015*((i-(W-1)/2.0)/max(1.0,W-1))
                mv = ((m + (0.5+mbias)*Lm + (0.5-mbias)*Rm) / 2.0) + R.uniform(-0.01, 0.01)
                new_ms[i] = max(0.0, min(1.0, mv))
            # advect mask slightly but weaker than color
            new_ms = [new_ms[i - int(round(0.35*u[i])) % W] for i in range(W)]

            # 8) gliders paint over (wrap footprint)
            alive = []
            for g in gliders:
                if not g.alive(): continue
                a = g.alpha()
                center = g.x; width = g.w
                # cover around center within 3*sigma
                span = int(3*width)+1
                for dj in range(-span, span+1):
                    j = int(round(center + dj)) % W
                    d = abs(dj)/max(1e-6, width)
                    w = a * math.exp(-0.5*d*d)
                    if w < 1e-3: continue
                    cnow = g.color_now(args.sat)
                    new_rgb[j] = [lerp(new_rgb[j][0], cnow[0], w),
                                  lerp(new_rgb[j][1], cnow[1], w),
                                  lerp(new_rgb[j][2], cnow[2], w)]
                    new_ms[j] = min(1.0, new_ms[j] + 0.25*w)
                g.step(W)
                if g.alive(): alive.append(g)
            gliders = alive

            # 9) tonal shaping
            new_rgb = apply_contrast_and_saturation(new_rgb, args.contrast, args.sat, args.chroma, args.gamma)

            # 10) paint
            out = []
            for i, v in enumerate(new_rgb):
                x = (i - (W-1)/2.0) / max(1.0, W-1)
                gate = mask_gate(new_ms[i], x)
                if new_ms[i] > gate:
                    out.append(paint(v, args.glyph, args.bg))
                else:
                    out.append(args.glyph)
            sys.stdout.write("".join(out) + "\n")

            rgb, ms = new_rgb, new_ms
            time.sleep(1.0/args.fps)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\x1b[0m\x1b[?25h")

if __name__ == "__main__":
    main()
