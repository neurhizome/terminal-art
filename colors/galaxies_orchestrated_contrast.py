#!/usr/bin/env python3
# Dusty's Orchestrated Galaxies — v5 (Contrast Edition)
# - Wider-spaced, punchier attractors
# - Temperature-sharpened softmax so winners dominate
# - Per-row contrast & saturation boosts (no external deps)
# - Chroma floor keeps colors from washing to pastel/gray

import sys, time, shutil, random as R, math

# ---------- knobs ----------
FPS = 60
GLYPH = "█"
USE_BG = False

# base color diffusion (horizontal)
DIVC_EPS_MAX = 0.06
DIVC_STEP = 0.0015
DIVC_WALK_CHANCE = 0.06
BASE_BIAS = 0.010
BIAS_GRAD = 0.015
POSTERIZE = 20                # chunkier bands -> more visible structure

# mask / gating (tears)
TARGET_LUMA = 112
GAIN = 0.02
MASK_DIV = 1.03
MASK_NOISE = 0.015
GATE = 0.52
GATE_STEP = 0.01
GATE_WALK_CHANCE = 0.20
CURVE = 0.28

# gliders
SPAWN_PROB = 0.06
SPAWN_NEAR_EDGE = 0.30
GLIDER_LIFE = (35, 120)
GLIDER_WIDTH = (4.0, 18.0)
DX_CHOICES = [-2.0, -1.0, -0.5, 0.5, 1.0, 2.0]
FADE_FRAC = 0.25
ALPHA_PEAK = 0.60              # stronger ink
MASK_BOOST = 0.28

# palette attractors (bold & far apart around the wheel)
ATTR = [
    (242, 63, 58),    # hot red
    (53, 220, 59),    # lime
    (63, 110, 255),   # deep blue
    (250, 210, 55),   # golden yellow
    (198, 63, 241),   # magenta
    (55, 238, 240),   # cyan
]
MUTATE = 0.025
PRESSURE = 0.52              # how strongly fitness reshapes weights
TEMP = 0.65                  # <1.0 sharpens softmax -> winner-take-most

# global tonal shaping
CONTRAST = 1.25              # scale around row-mean (1=no change)
SAT_BOOST = 1.35             # scale away from luma (1=no change)
CHROMA_FLOOR = 26.0          # enforce min distance from neutral (0..255)
GAMMA = 0.95                 # <1 brightens mids slightly

# ---------- helpers ----------
def term_width():
    try: return max(40, shutil.get_terminal_size().columns - 2)
    except: return 120

def clamp(x, lo=0, hi=255):
    return lo if x < lo else hi if x > hi else x

def paint(rgb, ch):
    r,g,b = (int(clamp(c)) for c in rgb)
    if USE_BG:
        return f"\x1b[48;2;{r};{g};{b}m{ch}\x1b[0m"
    else:
        return f"\x1b[38;2;{r};{g};{b}m{ch}\x1b[0m"

def mix3(me, L, Rr, eps, bias_x):
    wl = 0.5 + bias_x
    wr = 0.5 - bias_x
    w0 = 1.0
    d = 2.0 + eps
    return [
        (w0*me[0] + wl*L[0] + wr*Rr[0]) / d,
        (w0*me[1] + wl*L[1] + wr*Rr[1]) / d,
        (w0*me[2] + wl*L[2] + wr*Rr[2]) / d,
    ]

def mix1(me, L, Rr, div, bias_x):
    wl = 0.5 + bias_x
    wr = 0.5 - bias_x
    w0 = 1.0
    return (w0*me + wl*L + wr*Rr) / div

def luma(v):
    r,g,b=v; return 0.2126*r + 0.7152*g + 0.0722*b

def posterize(rgb, levels):
    step = 255.0/max(1,levels-1)
    return [int(round(c/step)*step) for c in rgb]

def line_brightness_adjust(row, target, gain):
    mean = sum(luma(v) for v in row) / len(row)
    k = 1.0 + gain * (target - mean) / 255.0
    return [[clamp(c*k) for c in v] for v in row]

def lerp(a,b,t): return a*(1-t)+b*t
def rgb_lerp(a,b,t): return [lerp(a[0],b[0],t), lerp(a[1],b[1],t), lerp(a[2],b[2],t)]
def rgb_dist(a,b): return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2) + 1e-6

def softmax_temp(z, temp):
    z = [v/max(1e-9,temp) for v in z]
    m = max(z)
    ez = [math.exp(v-m) for v in z]
    s = sum(ez); return [e/s for e in ez]

def apply_contrast_and_saturation(row):
    # contrast around per-row mean; saturation away from luma per-pixel
    # 1) contrast
    means = [sum(c)/3.0 for c in zip(*row)]  # per-channel mean to avoid hue shifts
    out = []
    for v in row:
        vv = [means[i] + (v[i]-means[i])*CONTRAST for i in range(3)]
        # 2) saturation boost relative to each pixel's gray level
        L = luma(vv)
        dv = [vv[0]-L, vv[1]-L, vv[2]-L]
        vv = [L + d*SAT_BOOST for d in dv]
        # 3) chroma floor (push away from neutral if too close)
        mag = math.sqrt(dv[0]**2 + dv[1]**2 + dv[2]**2)
        if mag < CHROMA_FLOOR and mag > 1e-6:
            s = CHROMA_FLOOR / mag
            vv = [L + (vv[0]-L)*s, L + (vv[1]-L)*s, L + (vv[2]-L)*s]
        # 4) simple gamma
        vv = [255.0*((clamp(c)/255.0)**GAMMA) for c in vv]
        out.append([clamp(c) for c in vv])
    return out

# ---------- glider entity ----------
class Glider:
    __slots__ = ("x","dx","life","age","w","col","col2")
    def __init__(self, x, dx, life, w, col, col2):
        self.x = x; self.dx = dx; self.life = life; self.age = 0
        self.w = w; self.col = col; self.col2 = col2
    def alive(self): return self.age < self.life
    def step(self):
        self.x += self.dx; self.age += 1
    def alpha(self):
        t = self.age / max(1, self.life-1)
        f = FADE_FRAC
        if t < f: a = t/f
        elif t > 1-f: a = (1-t)/f
        else: a = 1.0
        return ALPHA_PEAK * max(0.0, min(1.0, a))
    def color_now(self):
        t = self.age / max(1, self.life-1)
        base = rgb_lerp(self.col, self.col2, 0.5*t)
        # apply saturation boost so gliders never look washed out
        L = luma(base); dv = [base[0]-L, base[1]-L, base[2]-L]
        return [L + d*SAT_BOOST for d in dv]

# ---------- main ----------
def main():
    W = term_width()
    rgb = [[R.randint(0,255) for _ in range(3)] for _ in range(W)]
    ms  = [R.random() for _ in range(W)]
    gliders = []

    weights = [1/len(ATTR)] * len(ATTR)
    eps = 0.0
    sys.stdout.write("\x1b[?25l")
    try:
        while True:
            # fitness = inverse distance to attractors
            fit = []
            for a in ATTR:
                s = 0.0
                for v in rgb[::max(1, W//120)]:
                    s += 1.0 / rgb_dist(v, a)
                fit.append(s)
            fit = softmax_temp(fit, TEMP)
            mutated = [(w + R.uniform(-MUTATE, MUTATE)) for w in weights]
            mutated = [max(1e-6, m) for m in mutated]
            s = sum(mutated); mutated = [m/s for m in mutated]
            weights = [lerp(mutated[i], fit[i], PRESSURE) for i in range(len(ATTR))]
            sw = sum(weights); weights = [w/sw for w in weights]

            # color divisor walk
            if R.random() < DIVC_WALK_CHANCE:
                eps += R.choice([-1,0,1]) * DIVC_STEP
                eps = max(-DIVC_EPS_MAX, min(DIVC_EPS_MAX, eps))

            # gate walk
            global GATE
            if R.random() < GATE_WALK_CHANCE:
                GATE = max(0.25, min(0.75, GATE + R.choice([-1,1])*GATE_STEP))

            # spawn glider
            if R.random() < SPAWN_PROB:
                if R.random() < SPAWN_NEAR_EDGE:
                    candidates = [i for i,v in enumerate(ms) if abs(v-GATE) < 0.03]
                    x = float(R.choice(candidates)) if candidates else float(R.randint(0,W-1))
                else:
                    x = float(R.randint(0, W-1))
                dx = R.choice(DX_CHOICES)
                life = R.randint(*GLIDER_LIFE)
                w    = R.uniform(*GLIDER_WIDTH)
                ahead = int(min(W-1, max(0, round(x + 2*dx))))
                local = rgb[ahead][:]
                # choose attractor by weights
                r = R.random(); s=0.0; k=0
                for i,wgt in enumerate(weights):
                    s+=wgt
                    if r<=s: k=i; break
                toward = ATTR[k]
                gliders.append(Glider(x, dx, life, w, local, toward))

            # color diffusion
            new_rgb = []
            for i, me in enumerate(rgb):
                Lc = rgb[i-1] if i>0 else rgb[i]
                Rc = rgb[i+1] if i<W-1 else rgb[i]
                x = (i - (W-1)/2.0) / max(1.0, W-1)
                bias_x = BASE_BIAS + BIAS_GRAD * x
                v = mix3(me, Lc, Rc, eps, bias_x)
                new_rgb.append(v)
            new_rgb = [posterize(v, POSTERIZE) for v in new_rgb]
            new_rgb = line_brightness_adjust(new_rgb, TARGET_LUMA, GAIN)

            # mask transport
            new_ms = []
            for i, m in enumerate(ms):
                Lm = ms[i-1] if i>0 else ms[i]
                Rm = ms[i+1] if i<W-1 else ms[i]
                x = (i - (W-1)/2.0) / max(1.0, W-1)
                mbias = (BASE_BIAS*0.7) + BIAS_GRAD*1.2*x
                mv = mix1(m, Lm, Rm, MASK_DIV, mbias) + R.uniform(-MASK_NOISE, MASK_NOISE)
                new_ms.append(max(0.0, min(1.0, mv)))

            # gliders apply
            alive = []
            for g in gliders:
                if not g.alive(): continue
                a = g.alpha()
                center = g.x
                for j in range(int(max(0, center-3*g.w)), int(min(W-1, center+3*g.w))+1):
                    d = abs(j - center)/max(1e-6, g.w)
                    w = a * math.exp(-0.5*d*d)
                    if w < 1e-3: continue
                    cnow = g.color_now()
                    new_rgb[j] = [lerp(new_rgb[j][0], cnow[0], w),
                                  lerp(new_rgb[j][1], cnow[1], w),
                                  lerp(new_rgb[j][2], cnow[2], w)]
                    new_ms[j] = min(1.0, new_ms[j] + MASK_BOOST*w)
                g.step()
                if g.alive(): alive.append(g)
            gliders = alive

            # global contrast/saturation shaping (pre-mask)
            new_rgb = apply_contrast_and_saturation(new_rgb)

            # paint row
            out = []
            for i, v in enumerate(new_rgb):
                x = (i - (W-1)/2.0) / max(1.0, W-1)
                gate = GATE + CURVE*(x*x)
                if new_ms[i] > gate:
                    out.append(paint(v, GLYPH))
                else:
                    out.append(GLYPH)
            sys.stdout.write("".join(out) + "\n")

            rgb, ms = new_rgb, new_ms
            time.sleep(1.0/FPS)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\x1b[0m\x1b[?25h")

if __name__ == "__main__":
    main()
