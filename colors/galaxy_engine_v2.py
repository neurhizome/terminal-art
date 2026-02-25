#!/usr/bin/env python3
# Dusty's Galaxy Engine — v2
# Uniform glyph, "fireworks" reseeds, slow divisor drift near 2.0,
# slight spatial bias gradient, and posterization to encourage rings.
# Designed for iSH/a-Shell on iOS. Ctrl-C to quit.

import sys, time, shutil, random as R

# ---- knobs ----
FPS = 30
GLYPH = "█"              # uniform glyph so color field reads cleanly
USE_BG = False           # flip True to color the background instead

SEED_PROB = 2.0e-3       # base random speck probability per cell per row
BURST_PROB = 0.05        # chance per row to spawn a local "firework" burst
BURST_W_MIN = 4          # min width of burst
BURST_W_MAX = 18         # max width of burst

DIV_JITTER_MAX = 0.10    # |d_eps| <= this (so divisor in [1.90, 2.10])
DIV_STEP = 0.002         # step size when the divisor wanders
DIV_WALK_CHANCE = 0.06   # how often per row to nudge the divisor

BIAS_BASE = 0.020        # baseline left/right tilt (positive drifts right)
BIAS_FLIP_EVERY = 40     # rows between sign flips
BIAS_GRAD = 0.020        # adds a tiny spatial gradient to bias across columns

POSTERIZE = 28           # number of levels per channel (bands!)
TARGET_LUMA = 116        # line setpoint (0..255), keeps things from washing out
GAIN = 0.020             # how strongly to pull the line luma back

# ---- helpers ----
def term_width():
    try:
        return max(40, shutil.get_terminal_size().columns - 2)
    except Exception:
        return 120

def clamp(x, lo=0, hi=255): 
    return lo if x < lo else hi if x > hi else x

def paint(rgb, ch):
    r, g, b = (int(clamp(c)) for c in rgb)
    if USE_BG:
        return f"\x1b[48;2;{r};{g};{b}m{ch}\x1b[0m"
    else:
        return f"\x1b[38;2;{r};{g};{b}m{ch}\x1b[0m"

def luma(v):
    r,g,b=v; return 0.2126*r + 0.7152*g + 0.0722*b

def posterize(rgb, levels):
    step = 255.0/max(1,levels-1)
    return [int(round(c/step)*step) for c in rgb]

def mix(center, left, right, d_eps, bias_x):
    # asymmetric 3-tap with near-2.0 divisor
    wl = 0.5 + bias_x
    wr = 0.5 - bias_x
    w0 = 1.0
    d = 2.0 + d_eps
    return [
        (w0*center[0] + wl*left[0] + wr*right[0]) / d,
        (w0*center[1] + wl*left[1] + wr*right[1]) / d,
        (w0*center[2] + wl*left[2] + wr*right[2]) / d,
    ]

def line_brightness_adjust(row, target, gain):
    mean = sum(luma(v) for v in row) / len(row)
    k = 1.0 + gain * (target - mean) / 255.0
    return [[clamp(c*k) for c in v] for v in row]

def reseed():
    return [R.randint(0,255), R.randint(0,255), R.randint(0,255)]

# ---- main ----
def main():
    W = term_width()
    row = [[R.randint(0,255) for _ in range(3)] for _ in range(W)]
    d_eps = 0.0
    t = 0

    # hide cursor
    sys.stdout.write("\x1b[?25l")
    try:
        while True:
            # divisor performs a slow random walk near 2.0
            if R.random() < DIV_WALK_CHANCE:
                d_eps += R.choice([-1, 0, 1]) * DIV_STEP
                d_eps = max(-DIV_JITTER_MAX, min(DIV_JITTER_MAX, d_eps))

            # bias flips sign every so often; creates opposing shears
            sgn = 1 if ((t // BIAS_FLIP_EVERY) % 2)==0 else -1
            bias = sgn * BIAS_BASE

            # maybe spawn a "burst" (local reseed region)
            burst = None
            if R.random() < BURST_PROB:
                w = R.randint(BURST_W_MIN, BURST_W_MAX)
                c = R.randint(0, W-1)
                burst = (max(0,c-w//2), min(W-1, c+w//2))

            new = []
            for i, me in enumerate(row):
                L = row[i-1] if i>0 else row[i]
                Rr = row[i+1] if i<W-1 else row[i]

                # bias gradient bends ring families into ellipses
                x = (i - (W-1)/2.0) / max(1.0, W-1)
                bias_x = bias + BIAS_GRAD * x

                v = mix(me, L, Rr, d_eps, bias_x)

                # specks + bursts
                if burst and burst[0] <= i <= burst[1]:
                    if R.random() < 0.6:      # dense inside the burst window
                        v = reseed()
                elif R.random() < SEED_PROB:
                    v = reseed()

                new.append(posterize(v, POSTERIZE))

            # keep line luma in a lively band
            new = line_brightness_adjust(new, TARGET_LUMA, GAIN)

            # draw one uniform glyph across the row
            out = "".join(paint(v, GLYPH) for v in new)
            sys.stdout.write(out + "\n")

            row = new
            t += 1
            time.sleep(1.0 / FPS)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\x1b[0m\x1b[?25h")

if __name__ == "__main__":
    main()
