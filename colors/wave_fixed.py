
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
wave_fixed.py
Wave Interference Galaxy — multiple traveling waves interfere on a 1‑D ring.
Truecolor ANSI output; defaults to coloring the background of space characters
(works nicely on mobile terminals). Auto-width; wrap-aware.

Usage:
  python3 wave_fixed.py
  python3 wave_fixed.py --waves 6 --fps 60 --scroll 0.4 --fg --glyph "█"

Stdlib only.
"""
import sys, time, math, random, argparse, shutil

ESC   = "\x1b["
RESET = "\x1b[0m"

def term_width(margin:int=1) -> int:
    cols = shutil.get_terminal_size((80,24)).columns
    return max(20, cols - margin)

def hsv_to_rgb(h, s, v):
    # h in [0,1), s,v in [0,1]
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

def bg(r,g,b): return f"\x1b[48;2;{int(r)};{int(g)};{int(b)}m"
def fg(r,g,b): return f"\x1b[38;2;{int(r)};{int(g)};{int(b)}m"

def main():
    ap = argparse.ArgumentParser(description="Wave Interference Galaxy (1-D ring)")
    ap.add_argument("--fps", type=float, default=48.0)
    ap.add_argument("--width", type=int, default=0)
    ap.add_argument("--margin", type=int, default=1)
    ap.add_argument("--waves", type=int, default=4, help="number of traveling waves")
    ap.add_argument("--fg", action="store_true", help="use foreground glyph instead of background space")
    ap.add_argument("--glyph", type=str, default="█")
    ap.add_argument("--val", type=float, default=0.98, help="value/brightness")
    ap.add_argument("--sat-min", type=float, default=0.65)
    ap.add_argument("--sat-max", type=float, default=0.95)
    ap.add_argument("--scroll", type=float, default=0.30, help="diagonal slope via index phase per frame")
    ap.add_argument("--duration", type=float, default=0.0, help="seconds; 0=infinite")
    args = ap.parse_args()

    W = args.width if args.width>0 else term_width(args.margin)
    use_bg = not args.fg
    glyph = args.glyph[0] if args.glyph else "█"

    # Build waves: freq in cycles across ring; speed in radians/frame; hue distributed around cool wheel
    waves = []
    base_hues = [190, 210, 240, 280, 320, 350]
    random.shuffle(base_hues)
    for k in range(args.waves):
        freq = random.uniform(0.5, 3.5)    # cycles around the ring
        speed = random.uniform(0.02, 0.20) * random.choice([-1,1])
        phase0 = random.random() * 2*math.pi
        amp = random.uniform(0.6, 1.2)
        hue_deg = (base_hues[k % len(base_hues)] + random.uniform(-12, 12)) % 360.0
        decay = random.uniform(0.0005, 0.003)  # soft amplitude drift
        waves.append(dict(freq=freq, speed=speed, phase=phase0, amp=amp, hue_deg=hue_deg, decay=decay))

    # Frame loop
    t = 0
    dt = 1.0 / max(1.0, args.fps)
    sys.stdout.write("\x1b[?25l")  # hide cursor
    try:
        while True:
            # optional time limit
            # precompute hue unit vectors for each wave
            hv = []
            for w in waves:
                ang = math.radians(w["hue_deg"] % 360.0)
                hv.append((math.cos(ang), math.sin(ang)))

            idx_phase = (t * args.scroll) % W

            line_rgb = [None] * W
            for i in range(W):
                x = i / W
                # phase-advanced index for diagonal drift
                x2 = ((i + idx_phase) % W) / W

                # accumulate color vector and intensity from all waves
                vx = 0.0; vy = 0.0; pow_sum = 0.0
                for w, (ux,uy) in zip(waves, hv):
                    # traveling wave: sin(2π f x + φ + ω t)
                    theta = 2*math.pi*w["freq"]*x2 + w["phase"] + w["speed"]*t
                    s = math.sin(theta)
                    # positive energy contribution; square for sharper interference
                    energy = max(0.0, s) ** 2
                    weight = w["amp"] * energy
                    vx += weight * ux
                    vy += weight * uy
                    pow_sum += weight

                if pow_sum <= 1e-9:
                    h = 0.0; s = 0.0
                else:
                    # combined hue from vector sum
                    h = (math.degrees(math.atan2(vy, vx)) + 360.0) % 360.0
                    h = (h / 360.0) % 1.0
                    # saturation rises with interference intensity, bounded by sat range
                    inten = min(1.0, pow_sum / (args.waves * 1.2))
                    s = args.sat_min + (args.sat_max - args.sat_min) * inten

                r,g,b = hsv_to_rgb(h, s, args.val)
                line_rgb[i] = (r,g,b)

            # gentle drift of waves (prevent stasis)
            for w in waves:
                w["amp"] = max(0.3, min(1.4, w["amp"] * (1.0 - w["decay"] + random.uniform(-0.001, 0.001))))
                w["phase"] += random.uniform(-0.008, 0.008)

            # render
            out = []
            if use_bg:
                last = None
                for r,g,b in line_rgb:
                    if last != (r,g,b):
                        out.append(bg(r,g,b)); last=(r,g,b)
                    out.append(" ")
                out.append(RESET+"\n")
            else:
                for r,g,b in line_rgb:
                    out.append(fg(r,g,b) + glyph)
                out.append(RESET+"\n")

            sys.stdout.write("".join(out))
            sys.stdout.flush()

            t += 1
            if args.duration>0 and t*dt >= args.duration:
                break
            time.sleep(dt)

    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write(RESET + "\x1b[?25h")

if __name__ == "__main__":
    main()
