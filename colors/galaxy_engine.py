#!/usr/bin/env python3
# Dusty's Galaxy Engine — iOS friendly (iSH / a-Shell) — no deps, just ANSI 24-bit.
# Ctrl-C to stop.

import sys, time, shutil, random as R

# --- config you might tweak ---
FPS = 30                    # frame rate-ish
BIAS_WOBBLE = 0.015         # magnitude of left/right drift (small = gentle)
DIV_JITTER_MAX = 0.08       # how far the per-row divisor can wander from 2.0
SEED_PROB = 1.5e-3          # chance to reseed a pixel each frame
TARGET_LUMA = 116           # line-wide brightness setpoint (0..255)
GAIN = 0.02                 # how strongly we pull toward setpoint each row
GLYPHS = "░▒▓▞▚▙▛▜▟█▐▌"      # one glyph chosen per row (keeps that "striped rain" feel)
USE_BG = False              # if True, color background blocks; else color glyph fg

# --- helpers ---
def term_width():
    try:
        return max(40, shutil.get_terminal_size().columns - 2)
    except Exception:
        return 120

def clamp(x, lo=0, hi=255):
    return lo if x < lo else hi if x > hi else x

def paint_rgb(rgb, ch):
    r, g, b = (int(clamp(c)) for c in rgb)
    if USE_BG:
        return f"\x1b[48;2;{r};{g};{b}m{ch}\x1b[0m"
    else:
        return f"\x1b[38;2;{r};{g};{b}m{ch}\x1b[0m"

def mix(center, left, right, d_eps, bias):
    # weights: me + left + right with a tiny tilt; divide by ~2 (+/- eps)
    wl = 0.5 + bias
    wr = 0.5 - bias
    w0 = 1.0
    d = 2.0 + d_eps
    return [
        (w0*center[0] + wl*left[0] + wr*right[0]) / d,
        (w0*center[1] + wl*left[1] + wr*right[1]) / d,
        (w0*center[2] + wl*left[2] + wr*right[2]) / d,
    ]

def luma(v):
    # perceptual-ish luminance
    r,g,b = v
    return 0.2126*r + 0.7152*g + 0.0722*b

def line_brightness_adjust(row, target, gain):
    mean = sum(luma(v) for v in row) / len(row)
    k = 1.0 + gain * (target - mean) / 255.0
    return [[clamp(c*k) for c in v] for v in row]

def reseed(v):
    return [R.randint(0,255), R.randint(0,255), R.randint(0,255)]

# --- main loop ---
def main():
    W = term_width()
    row = [[R.randint(0,255) for _ in range(3)] for _ in range(W)]

    d_eps = 0.0     # near-2 divisor offset (per-row)
    bias = 0.0      # left/right tilt (per-row)
    phase = 0       # just for slow wobbling of bias

    # hide cursor, restore on exit
    sys.stdout.write("\x1b[?25l")
    try:
        while True:
            # wander the divisor a little; hold steady-ish so bands can form
            if R.random() < 0.12:
                d_eps += R.choice([-1, -1, 0, 0, 1, 1]) * (DIV_JITTER_MAX/20.0)
                d_eps = max(-DIV_JITTER_MAX, min(DIV_JITTER_MAX, d_eps))

            # slow bias wobble back and forth (gliders + rings)
            phase += 1
            bias = BIAS_WOBBLE * ( ( (phase//27) % 2 )*2 - 1 )  # stair wobble

            # choose one glyph for the whole row (gives that "striped" look)
            g = R.choice(GLYPHS)

            # neighbor mix
            new = []
            for i, me in enumerate(row):
                L = row[i-1] if i > 0 else row[i]
                Rr = row[i+1] if i < W-1 else row[i]
                v = mix(me, L, Rr, d_eps, bias)
                if R.random() < SEED_PROB:
                    v = reseed(v)
                # quantize to 8-bit per channel to accent banding
                new.append([int(clamp(x)) for x in v])

            # line-wide integrator tug toward a setpoint
            new = line_brightness_adjust(new, TARGET_LUMA, GAIN)

            # paint & print
            if USE_BG:
                out = "".join(paint_rgb(v, " ") for v in new)
            else:
                out = "".join(paint_rgb(v, g) for v in new)
            sys.stdout.write(out + "\n")

            row = new
            time.sleep(1.0 / FPS)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\x1b[0m\x1b[?25h")

if __name__ == "__main__":
    main()
