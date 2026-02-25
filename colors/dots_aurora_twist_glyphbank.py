#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dots_aurora_twist_glyphbank.py — fast, resize‑aware aurora braids with glyph bank

Adds a glyph loader/curator so you can point at a big glyph file and
auto‑extract tasty tessellators while skipping letters/numbers.

Highlights:
• Live terminal resize (SIGWINCH) and full‑screen fit (alt screen by default).
• Smooth animation: sine LUT, hue cache, dirty‑row redraw, careful pacing.
• Speed knobs: --fps, --speed, --stride (horizontal), --vstride (vertical).
• Glyph sources:
    - Presets: ascii, dots, braid, blocks, contrast
    - --glyphs-custom "…"
    - --glyph-file /path/to/unicode_glyphs_full.txt with optional --glyph-theme
      Theme keywords choose subsets by Unicode name: box, block, braille,
      geo, tri, stars, spark, ding, line, shade, arrow, pattern

Examples:
  python3 dots_aurora_twist_glyphbank.py --fps 60 --speed 1.0
  python3 dots_aurora_twist_glyphbank.py --glyph-file unicode_glyphs_full.txt --glyph-theme box
  python3 dots_aurora_twist_glyphbank.py --glyphs-custom " ░▒▓█▚▞▟" --stride 2
"""

import argparse, math, os, random, signal, sys, time, unicodedata, re
from shutil import get_terminal_size

RESET = "\x1b[0m"
HIDE  = "\x1b[?25l"
SHOW  = "\x1b[?25h"
ALT_ON  = "\x1b[?1049h"
ALT_OFF = "\x1b[?1049l"

def clamp(x, a, b):
    return a if x < a else b if x > b else x

def hsv_to_rgb(h, s, v):
    i = int(h*6.0) % 6
    f = h*6.0 - int(h*6.0)
    p = v*(1.0 - s)
    q = v*(1.0 - f*s)
    t = v*(1.0 - (1.0 - f)*s)
    if   i == 0: r,g,b = v,t,p
    elif i == 1: r,g,b = q,v,p
    elif i == 2: r,g,b = p,v,t
    elif i == 3: r,g,b = p,q,v
    elif i == 4: r,g,b = t,p,v
    else:        r,g,b = v,p,q
    return int(r*255), int(g*255), int(b*255)

def fg_rgb(r,g,b): return f"\x1b[38;2;{r};{g};{b}m"
def bg_rgb(r,g,b): return f"\x1b[48;2;{r};{g};{b}m"

GLYPH_PRESETS = {
    "dots":     "·•*✶✷✸✹✺✻✼",
    "braid":    " .:/╱╲│─┼╳",
    "blocks":   "░▒▓█",
    "contrast": " ▖▗▘▝▚▞▟█",
    "ascii":    " .:-=+*#%@",
}

# ---------- fast trig & palettes ----------
LUT_SIZE = 8192
TAU = math.tau if hasattr(math, "tau") else 2*math.pi
_sin_lut = [math.sin(TAU * i / LUT_SIZE) for i in range(LUT_SIZE)]
def fast_sin(x):
    y = x % TAU
    return _sin_lut[int(y * (LUT_SIZE/TAU)) & (LUT_SIZE-1)]

class HueCache:
    def __init__(self, s=0.9, v=0.95, bg_scale=0.55):
        self.s, self.v = clamp(s,0,1), clamp(v,0,1)
        self.bg_scale = bg_scale
        self.steps = 720
        self.fg = [None]*self.steps
        self.bg = [None]*self.steps

    def get_codes(self, h, use_bg, g_norm):
        idx = int((h % 1.0) * self.steps) % self.steps
        if self.fg[idx] is None:
            r,g,b = hsv_to_rgb(idx/self.steps, self.s, self.v)
            self.fg[idx] = fg_rgb(r,g,b)
            br,bg,bb = hsv_to_rgb(((idx/self.steps)+0.5)%1.0, self.s*self.bg_scale, 0.18 + 0.18*g_norm)
            self.bg[idx] = bg_rgb(br,bg,bb)
        return (self.bg[idx] if use_bg else ""), self.fg[idx]

# ---------- field math ----------
def orbit(t, w, h, phase, rx=0.38, ry=0.22):
    cx, cy = w*0.5, h*0.5
    x = cx + math.cos(t + phase*1.7)*w*rx
    y = cy + math.sin(t*0.8 + phase*2.3)*h*ry
    return x, y

def field_value(x, y, t, w, h, scale):
    ax, ay = orbit(t*0.9, w, h, 0.0)
    bx, by = orbit(t*1.1, w, h, 1.3)
    da = math.hypot(x-ax, y-ay)
    db = math.hypot(x-bx, y-by)
    v  = fast_sin(da*scale + t*0.9) + fast_sin(db*scale*1.1 - t*1.1)
    curl = fast_sin((x*0.013 + y*0.021) + fast_sin(t*0.33)*1.7)
    return v + 0.35*curl

# ---------- glyph loader/curator ----------
_THEME_MAP = {
    "box":    ("BOX", "DRAWINGS", "LIGHT", "HEAVY", "ARC", "QUADRANT"),
    "block":  ("BLOCK", "ELEMENT", "FULL", "HALF"),
    "braille":("BRAILLE",),
    "geo":    ("GEOMETRIC", "CIRCLE", "SQUARE", "DIAMOND", "BLACK", "WHITE"),
    "tri":    ("TRIANGLE", "DELTA"),
    "stars":  ("STAR",),
    "spark":  ("ASTERISK", "EIGHT", "SPARKLE", "SNOW"),
    "ding":   ("DINGBAT", "ORNAMENT"),
    "line":   ("HORIZONTAL", "VERTICAL", "RULE", "BOX DRAWINGS"),
    "shade":  ("SHADE", "SHADING"),
    "arrow":  ("ARROW", "ARROWS", "TRIANGLE-HEADED"),
    "pattern":("TILE", "PATTERN", "HATCH"),
}

def curate_from_file(path, theme=None, limit=None, shuffle=False):
    try:
        data = Path(path).read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        return None
    # Extract characters from the file, skipping plain ASCII letters/numbers and whitespace.
    # Keep only printable non-control, non-mark symbols and punctuation.
    out = []
    seen = set()
    for ch in data:
        if ch in seen: 
            continue
        if ch.isspace():
            continue
        cat = unicodedata.category(ch)  # e.g., 'Lu','Ll','Nd','Po','So', etc.
        if not cat: 
            continue
        if cat[0] in ("L","N","C","M","Z"):  # skip letters, numbers, controls, marks, separators
            continue
        # crude width filter: skip emoji (often 'So' with name containing 'EMOJI') to avoid width surprises
        name = unicodedata.name(ch, "")
        if "EMOJI" in name or "FACE" in name or "HAND" in name:
            continue
        # simple printable gate
        try:
            _ = f"{ch}"
        except Exception:
            continue
        seen.add(ch)
        out.append((ch, name))
    # Optional theme filter by Unicode name keywords
    if theme:
        keys = _THEME_MAP.get(theme.lower(), None)
        if keys:
            pat = re.compile("|".join(re.escape(k) for k in keys))
            themed = [ch for ch,name in out if pat.search(name)]
            if len(themed) >= 2:
                out = [(ch, unicodedata.name(ch,"")) for ch in themed]
    # Order: keep file order unless we shuffle
    chars = [ch for ch,_ in out]
    if shuffle:
        random.Random(1337).shuffle(chars)
    # Optional limit to keep the set tight and performant
    if limit and limit > 0:
        chars = chars[:limit]
    # collapse to string, ensure at least 2 glyphs
    unique = "".join(chars)
    return unique if len(unique) >= 2 else None

# ---------- resize/render loop ----------
_resized = True
def _mark_resized(signum=None, frame=None):
    global _resized
    _resized = True

def get_dims():
    ts = get_terminal_size((120, 40))
    cols = max(40, ts.columns)
    rows = max(8, ts.lines - 1)  # leave 1-line margin
    return cols, rows

def build_args():
    ap = argparse.ArgumentParser(description="Aurora braids + glyph bank")
    ap.add_argument("--fps", type=float, default=60.0)
    ap.add_argument("--speed", type=float, default=0.9)
    ap.add_argument("--scale", type=float, default=0.034, help="distance scale")
    ap.add_argument("--saturation", type=float, default=0.88)
    ap.add_argument("--value", type=float, default=0.96)
    ap.add_argument("--glyphs", type=str, default="ascii", choices=sorted(GLYPH_PRESETS.keys()))
    ap.add_argument("--glyphs-custom", type=str, default=None)
    ap.add_argument("--glyph-file", type=str, default=None, help="path to glyph dump text")
    ap.add_argument("--glyph-theme", type=str, default=None, help="theme keyword (box, block, braille, geo, tri, stars, spark, ding, line, shade, arrow, pattern)")
    ap.add_argument("--glyph-limit", type=int, default=64, help="keep first N curated glyphs")
    ap.add_argument("--glyph-shuffle", action="store_true", help="shuffle curated glyphs for variety")
    ap.add_argument("--stride", type=int, default=1, help="horizontal sampling stride (≥1)")
    ap.add_argument("--vstride", type=int, default=1, help="vertical sampling stride (≥1)")
    ap.add_argument("--no-bg", action="store_true")
    ap.add_argument("--no-alt", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    return ap.parse_args()

def choose_glyphs(args):
    # Priority: custom string > file > preset
    if args.glyphs_custom:
        g = args.glyphs_custom
        return g if len(g) >= 2 else GLYPH_PRESETS["ascii"]
    if args.glyph_file:
        g = curate_from_file(args.glyph_file, theme=args.glyph_theme, limit=args.glyph_limit, shuffle=args.glyph_shuffle)
        if g: 
            return g
    return GLYPH_PRESETS[args.glyphs]

def main():
    global _resized
    args = build_args()
    if args.seed is not None:
        random.seed(args.seed)

    glyphs = choose_glyphs(args)
    G = max(1, len(glyphs) - 1)

    try:
        signal.signal(signal.SIGWINCH, _mark_resized)
    except Exception:
        pass

    hue_cache = HueCache(args.saturation, args.value, bg_scale=0.55)
    use_bg = (not args.no_bg)

    if not args.no_alt:
        sys.stdout.write(ALT_ON)
    sys.stdout.write(HIDE)
    sys.stdout.flush()

    cols, rows = get_dims()
    last_rows = [""] * rows

    stride = max(1, int(args.stride))
    vstride = max(1, int(args.vstride))

    target_dt = 1.0 / max(1e-3, args.fps)
    t = 0.0
    last = time.perf_counter()

    try:
        sys.stdout.write("\x1b[2J\x1b[H")
        sys.stdout.flush()

        while True:
            now = time.perf_counter()
            dt = now - last
            last = now
            t += dt * args.speed

            if _resized:
                _resized = False
                cols, rows = get_dims()
                last_rows = [""] * rows
                sys.stdout.write("\x1b[2J\x1b[H")
                sys.stdout.flush()

            w = cols
            h = rows

            new_rows = [None] * rows
            j = 0
            while j < rows:
                y = (j + 0.37) * 1.0
                row_chars = []
                i = 0
                while i < cols:
                    x = (i + 0.53) * 1.0
                    v = field_value(x, y, t, w, h, args.scale)

                    gidx = int(clamp((v*0.5 + 0.5) * G + 0.5, 0, G))
                    g_norm = (gidx / G) if G > 0 else 0.0
                    hue  = (0.62 + 0.40*(v*0.5 + 0.5) + (j/rows)*0.12) % 1.0

                    bgc, fgc = hue_cache.get_codes(hue, use_bg, g_norm)
                    cell = f"{bgc}{fgc}{glyphs[gidx]}"
                    # horizontal span
                    span = min(stride, cols - i)
                    row_chars.append(cell * span)
                    i += span

                line = "".join(row_chars) + RESET
                # vertical span: duplicate this line vstride times (but cap inside rows)
                rep = min(vstride, rows - j)
                for k in range(rep):
                    new_rows[j+k] = line
                j += rep

            # repaint only changed rows
            for r in range(rows):
                if new_rows[r] != (last_rows[r] if r < len(last_rows) else ""):
                    sys.stdout.write(f"\x1b[{r+1};1H")
                    sys.stdout.write(new_rows[r])

            sys.stdout.flush()
            last_rows = new_rows

            sleep_for = target_dt - (time.perf_counter() - now)
            if sleep_for > 0:
                time.sleep(min(sleep_for, 0.010))

    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write(RESET + SHOW)
        if not args.no_alt:
            sys.stdout.write(ALT_OFF)
        sys.stdout.flush()

if __name__ == "__main__":
    main()
