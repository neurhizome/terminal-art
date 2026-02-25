#!/usr/bin/env python3
# Dusty's Orchestrated Galaxies — v4
# Goals:
#  - uniform glyph (color field only) so color reads clearly
#  - "sparks" (gliders) are NOT random; they pre-sample the field ahead,
#    pick colors influenced by local context + global attractor weights,
#    and fade-in/out while drifting diagonally at pre-quantized slopes.
#  - separate ON/OFF mask creates ring/tear bands with curvature
#  - tiny evolutionary game keeps a palette of attractors competing
# Designed for iSH/a-Shell on iOS. Ctrl-C to quit.

import sys, time, shutil, random as R, math

# ---------- knobs ----------
FPS = 30
GLYPH = "█"
USE_BG = False                 # True = background blocks, False = colored glyphs

# base color diffusion (horizontal)
DIVC_EPS_MAX = 0.06           # |divisor offset|; mixing divisor = 2.0 + eps
DIVC_STEP = 0.0015
DIVC_WALK_CHANCE = 0.06
BASE_BIAS = 0.010             # small left/right tilt
BIAS_GRAD = 0.015             # curve the family of rings into ellipses
POSTERIZE = 26                # banding

# mask/gating for "tears"
TARGET_LUMA = 116
GAIN = 0.02
MASK_DIV = 1.03               # sharper than color
MASK_NOISE = 0.015
GATE = 0.52                   # per-row threshold in [0,1]
GATE_STEP = 0.01
GATE_WALK_CHANCE = 0.20
CURVE = 0.28                  # ellipse curvature across row

# gliders (“fireworks” that fade/flow)
SPAWN_PROB = 0.06             # chance per row to spawn a glider somewhere
SPAWN_NEAR_EDGE = 0.25        # prefer spawning near mask edges
GLIDER_LIFE = (35, 120)       # min/max rows of life
GLIDER_WIDTH = (4.0, 18.0)    # visual width for blending
# quantized slopes (columns per row). fractionals give steep diagonals
DX_CHOICES = [-2.0, -1.0, -0.5, 0.5, 1.0, 2.0]
FADE_FRAC = 0.25              # portion of life used to fade in/out
ALPHA_PEAK = 0.50             # blend strength at glider center (0..1)
MASK_BOOST = 0.25             # glider lifts mask to ensure visibility

# evolutionary attractors (RGB anchors); weights mutate/compete
ATTR = [
    (230, 80, 80),    # ember
    (64, 140, 255),   # cobalt
    (40, 205, 140),   # seafoam
    (165, 90, 210),   # amethyst
    (240, 170, 70),   # apricot
    (70, 210, 210),   # cyan
]
MUTATE = 0.04              # per-row mutation rate for attractor weights
PRESSURE = 0.30            # how strongly fitness reshapes weights (0..1)

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

def rgb_lerp(a,b,t):
    return [lerp(a[0],b[0],t), lerp(a[1],b[1],t), lerp(a[2],b[2],t)]

def rgb_dist(a,b):
    return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2) + 1e-6

def softmax(z):
    m = max(z)
    ez = [math.exp(v-m) for v in z]
    s = sum(ez); return [e/s for e in ez]

# ---------- glider entity ----------
class Glider:
    __slots__ = ("x","dx","life","age","w","col","col2")  # col2 = toward attractor
    def __init__(self, x, dx, life, w, col, col2):
        self.x = x; self.dx = dx; self.life = life; self.age = 0
        self.w = w; self.col = col; self.col2 = col2
    def alive(self): return self.age < self.life
    def step(self):
        self.x += self.dx
        self.age += 1
    def alpha(self):
        # fade in/out envelope
        t = self.age / max(1, self.life-1)
        f = FADE_FRAC
        if t < f: a = t/f
        elif t > 1-f: a = (1-t)/f
        else: a = 1.0
        return ALPHA_PEAK * max(0.0, min(1.0, a))
    def color_now(self):
        # slide from local-sampled color toward attractor color across lifetime
        t = self.age / max(1, self.life-1)
        return rgb_lerp(self.col, self.col2, 0.4*t)

# ---------- main ----------
def main():
    W = term_width()
    rgb = [[R.randint(0,255) for _ in range(3)] for _ in range(W)]
    ms  = [R.random() for _ in range(W)]
    gliders = []

    # evolutionary palette weights
    weights = [1/len(ATTR)] * len(ATTR)

    # color mixing state
    eps = 0.0
    t = 0

    sys.stdout.write("\x1b[?25l")
    try:
        while True:
            # --- evolve attractor weights (“fitness” = how much of the row is near that attractor) ---
            fit = []
            for a in ATTR:
                # inverse average distance
                s = 0.0
                for v in rgb[::max(1, W//120)]:  # sample to lighten CPU
                    s += 1.0 / rgb_dist(v, a)
                fit.append(s)
            fit = softmax(fit)
            # mutate a bit and blend with fitness
            mutated = [(w + R.uniform(-MUTATE, MUTATE)) for w in weights]
            mutated = [max(1e-6, m) for m in mutated]
            s = sum(mutated); mutated = [m/s for m in mutated]
            weights = [lerp(mutated[i], fit[i], PRESSURE) for i in range(len(ATTR))]
            sw = sum(weights); weights = [w/sw for w in weights]

            # --- color-field divisor small random walk ---
            if R.random() < DIVC_WALK_CHANCE:
                eps += R.choice([-1,0,1]) * DIVC_STEP
                eps = max(-DIVC_EPS_MAX, min(DIVC_EPS_MAX, eps))

            # --- per-row gate walk (horizontal coherence) ---
            global GATE
            if R.random() < GATE_WALK_CHANCE:
                GATE = max(0.25, min(0.75, GATE + R.choice([-1,1])*GATE_STEP))

            # --- maybe spawn a glider ---
            if R.random() < SPAWN_PROB:
                # choose an x: either near a mask edge, or anywhere
                if R.random() < SPAWN_NEAR_EDGE:
                    # find index where mask is near gate (edge)
                    candidates = [i for i,v in enumerate(ms) if abs(v-GATE) < 0.03]
                    x = float(R.choice(candidates)) if candidates else float(R.randint(0,W-1))
                else:
                    x = float(R.randint(0, W-1))

                dx = R.choice(DX_CHOICES)
                life = R.randint(*GLIDER_LIFE)
                w    = R.uniform(*GLIDER_WIDTH)
                # pre-sample color *ahead* of trajectory
                ahead = int(min(W-1, max(0, round(x + 2*dx))))
                local = rgb[ahead][:]
                # choose an attractor with current weights
                r = R.random(); s=0.0; k=0
                for i,wgt in enumerate(weights):
                    s+=wgt
                    if r<=s: k=i; break
                toward = ATTR[k]
                gliders.append(Glider(x, dx, life, w, local, toward))

            # --- color diffusion pass ---
            new_rgb = []
            for i, me in enumerate(rgb):
                L = rgb[i-1] if i>0 else rgb[i]
                Rr = rgb[i+1] if i<W-1 else rgb[i]
                x = (i - (W-1)/2.0) / max(1.0, W-1)
                bias_x = BASE_BIAS + BIAS_GRAD * x
                v = mix3(me, L, Rr, eps, bias_x)
                new_rgb.append(v)
            new_rgb = [posterize(v, POSTERIZE) for v in new_rgb]
            new_rgb = line_brightness_adjust(new_rgb, TARGET_LUMA, GAIN)

            # --- mask update (transport + noise) ---
            new_ms = []
            for i, m in enumerate(ms):
                L = ms[i-1] if i>0 else ms[i]
                Rr = ms[i+1] if i<W-1 else ms[i]
                x = (i - (W-1)/2.0) / max(1.0, W-1)
                mbias = (BASE_BIAS*0.7) + BIAS_GRAD*1.2*x
                mv = mix1(m, L, Rr, MASK_DIV, mbias) + R.uniform(-MASK_NOISE, MASK_NOISE)
                new_ms.append(max(0.0, min(1.0, mv)))

            # --- apply gliders (fade, drift, mask lift) ---
            alive = []
            for g in gliders:
                if not g.alive():
                    continue
                a = g.alpha()
                # paint a gaussian-ish footprint around g.x
                center = g.x
                for j in range(int(max(0, center-3*g.w)), int(min(W-1, center+3*g.w))+1):
                    d = abs(j - center)/max(1e-6, g.w)
                    w = a * math.exp(-0.5*d*d)
                    if w < 1e-3: 
                        continue
                    cnow = g.color_now()
                    new_rgb[j] = [lerp(new_rgb[j][0], cnow[0], w),
                                  lerp(new_rgb[j][1], cnow[1], w),
                                  lerp(new_rgb[j][2], cnow[2], w)]
                    new_ms[j] = min(1.0, new_ms[j] + MASK_BOOST*w)
                g.step()
                if g.alive():
                    alive.append(g)
            gliders = alive

            # --- paint row using mask gate with curvature (ellipse) ---
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
            t += 1
            time.sleep(1.0/FPS)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\x1b[0m\x1b[?25h")

if __name__ == "__main__":
    main()
