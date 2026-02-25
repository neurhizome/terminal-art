#!/usr/bin/env python3
# Dusty's Tearing Galaxies — v3
# Separate ON/OFF mask field creates "uncolored" bands; mask advects with bias & curvature.
# Color field evolves separately with near-2 mixing. Ctrl-C to quit.

import sys, time, shutil, random as R

# ---- knobs ----
FPS = 30
GLYPH = "█"            # one block everywhere
USE_BG = False         # color foreground by default; flip True to color background instead

# color-field dynamics
DIVC_JITTER_MAX = 0.08
DIVC_STEP = 0.002
DIVC_WALK_CHANCE = 0.08
BIAS_BASE = 0.018
BIAS_FLIP_EVERY = 48
BIAS_GRAD = 0.018
POSTERIZE = 26
TARGET_LUMA = 118
GAIN = 0.020

# mask-field dynamics (this makes the "tears" and rings)
DIVM = 1.04              # near-1 updates keep structure sharper than color field
MASK_BIAS_BASE = 0.012
MASK_BIAS_GRAD = 0.030
MASK_NOISE = 0.02        # small noise to keep things alive

# per-row gate controls ON/OFF; it wanders, making horizontal coherence
GATE = 0.52
GATE_STEP = 0.01
GATE_WALK_CHANCE = 0.25
CURVE = 0.25             # 0..~0.6; adds quadratic curvature across columns (ellipses)

# reseeding
SEED_PROB = 1.2e-3
BURST_PROB = 0.05
BURST_W_MIN = 5
BURST_W_MAX = 22

# ---- helpers ----
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

def luma(v):
    r,g,b=v; return 0.2126*r + 0.7152*g + 0.0722*b

def posterize(rgb, levels):
    step = 255.0/max(1,levels-1)
    return [int(round(c/step)*step) for c in rgb]

def mix3(me, L, Rr, div_eps, bias_x):
    wl = 0.5 + bias_x
    wr = 0.5 - bias_x
    w0 = 1.0
    d = 2.0 + div_eps
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

def line_brightness_adjust(row, target, gain):
    mean = sum(luma(v) for v in row) / len(row)
    k = 1.0 + gain * (target - mean) / 255.0
    return [[clamp(c*k) for c in v] for v in row]

def reseed_rgb():
    return [R.randint(0,255), R.randint(0,255), R.randint(0,255)]

def reseed_mask():
    return R.random()

# ---- main ----
def main():
    W = term_width()
    rgb = [[R.randint(0,255) for _ in range(3)] for _ in range(W)]
    ms  = [R.random() for _ in range(W)]

    divc_eps = 0.0
    gate = GATE
    t = 0

    # hide cursor
    sys.stdout.write("\x1b[?25l")
    try:
        while True:
            # color field divisor random walk
            if R.random() < DIVC_WALK_CHANCE:
                divc_eps += R.choice([-1,0,1]) * DIVC_STEP
                divc_eps = max(-DIVC_JITTER_MAX, min(DIVC_JITTER_MAX, divc_eps))

            # bias flip
            sgn = 1 if ((t // BIAS_FLIP_EVERY) % 2)==0 else -1
            bias_base = sgn * BIAS_BASE

            # per-row gate wanders (horizontal coherence)
            if R.random() < GATE_WALK_CHANCE:
                gate += R.choice([-1,1]) * GATE_STEP
                gate = max(0.25, min(0.75, gate))

            # maybe burst
            burst = None
            if R.random() < BURST_PROB:
                w = R.randint(BURST_W_MIN, BURST_W_MAX)
                c = R.randint(0, W-1)
                burst = (max(0,c-w//2), min(W-1, c+w//2))

            # update both fields
            new_rgb, new_ms = [], []
            for i in range(W):
                L = i-1 if i>0 else i
                Rr = i+1 if i<W-1 else i

                # spatial coordinate for curvature
                x = (i - (W-1)/2.0) / max(1.0, W-1)

                # color
                bias_x = bias_base + BIAS_GRAD * x
                v = mix3(rgb[i], rgb[L], rgb[Rr], divc_eps, bias_x)

                # mask scalar field (sharper transport, its own bias and noise)
                mbias_x = MASK_BIAS_BASE + MASK_BIAS_GRAD * x * sgn
                m = mix1(ms[i], ms[L], ms[Rr], DIVM, mbias_x) + R.uniform(-MASK_NOISE, MASK_NOISE)

                # reseeds
                if burst and burst[0] <= i <= burst[1]:
                    if R.random() < 0.6:
                        v = reseed_rgb()
                        m = reseed_mask()
                elif R.random() < SEED_PROB:
                    v = reseed_rgb()
                    m = reseed_mask()

                new_rgb.append(posterize(v, POSTERIZE))
                new_ms.append(max(0.0, min(1.0, m)))

            # line brightness control
            new_rgb = line_brightness_adjust(new_rgb, TARGET_LUMA, GAIN)

            # decide ON/OFF via gate + curvature (quadratic raises gate more at edges)
            out = []
            for i, v in enumerate(new_rgb):
                x = (i - (W-1)/2.0) / max(1.0, W-1)
                curved_gate = gate + CURVE * (x*x)  # ellipse flavor
                if new_ms[i] > curved_gate:
                    out.append(paint(v, GLYPH))     # colored ON
                else:
                    out.append(GLYPH)               # plain OFF (terminal default color)
            sys.stdout.write("".join(out) + "\n")

            rgb, ms = new_rgb, new_ms
            t += 1
            time.sleep(1.0 / FPS)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\x1b[0m\x1b[?25h")

if __name__ == "__main__":
    main()
