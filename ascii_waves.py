#!/usr/bin/env python3
# ascii_waves.py — modular ASCII/Unicode automata renderer
# No external dependencies. UTF‑8 output. iSH‑friendly.
import sys, os, math, time, shutil, random, argparse
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional

# ---------- Utilities ----------

def clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)

def clamp8(x: float) -> int:
    x = 0 if x < 0 else (255 if x > 255 else x)
    return int(x)

def rgb_tuple(r: float, g: float, b: float) -> Tuple[int,int,int]:
    return (clamp8(r*255), clamp8(g*255), clamp8(b*255))

def hsv_to_rgb(h: float, s: float, v: float) -> Tuple[int,int,int]:
    # standard HSV→RGB, h in [0,1)
    i = int(h*6.0) % 6
    f = h*6.0 - i
    p = v*(1.0 - s)
    q = v*(1.0 - f*s)
    t = v*(1.0 - (1.0-f)*s)
    if i == 0: r,g,b = v,t,p
    elif i == 1: r,g,b = q,v,p
    elif i == 2: r,g,b = p,v,t
    elif i == 3: r,g,b = p,q,v
    elif i == 4: r,g,b = t,p,v
    else: r,g,b = v,p,q
    return rgb_tuple(r,g,b)

def hsv_mix(hsvs: List[Tuple[float,float,float]], jitter: float) -> Tuple[float,float,float]:
    # Simple Dirichlet-ish random blend with circular hue mean.
    ws = [random.random() for _ in hsvs]
    s = sum(ws) or 1.0
    ws = [w/s for w in ws]
    xs = sum(w*math.cos(2*math.pi*h) for (w,(h,_,_)) in zip(ws, hsvs))
    ys = sum(w*math.sin(2*math.pi*h) for (w,(h,_,_)) in zip(ws, hsvs))
    h = (math.atan2(ys, xs) / (2*math.pi)) % 1.0
    s_ = sum(w*sv for w,(_,sv,_) in zip(ws, hsvs))
    v_ = sum(w*vv for w,(_,_,vv) in zip(ws, hsvs))
    vmax = max(v for _,_,v in hsvs)
    v = 0.80*vmax + 0.20*v_
    s = clamp01(s_*1.06)
    # jitter
    h = (h + random.uniform(-0.03*jitter, 0.03*jitter)) % 1.0
    s = clamp01(s + random.uniform(-0.04*jitter, 0.04*jitter))
    v = clamp01(v + random.uniform(-0.03*jitter, 0.03*jitter))
    return h, s, v

def anti_colors_from_fg(h: float, s: float, v: float) -> Tuple[Tuple[int,int,int], Tuple[int,int,int]]:
    # return (fg_rgb, bg_rgb) with anti/background pairing
    h2 = (h + 0.5) % 1.0   # opposite hue
    s2 = clamp01(0.60 + 0.35*(1.0-s))  # ensure bg is vivid but not neon
    v2 = clamp01(0.25 + 0.65*(1.0-v))  # darker/lighter contrast
    fr,fg,fb = hsv_to_rgb(h, s, v)
    br,bg,bb = hsv_to_rgb(h2, s2, v2)
    return (fr,fg,fb), (br,bg,bb)

# ---------- Glyph sets ----------
GLYPH_SETS: Dict[str, List[str]] = {
    "spaces": [" "],
    "dots": ["·","•","‧","∙","∘","·"],
    "angles": ["╱","╲","╳","╱","╲"],
    "pipes": ["│","─","┼","┤","├"],
    "blocks": ["█","▓","▒","░"],
    "shade": list(" .:-=+*#%@"),  # ascii density gradient
    "braille-lite": ["⣿","⣶","⣤","⣤","⣀","⠂","⠄","⠂"],
    "ascii": list(" .,:;+xX#"),
}

# Connector codes by NESW bitmask (up=1, right=2, down=4, left=8)
CODES: Dict[int, str] = {
    0b0000: "SP", 0b0001: "N", 0b0010: "E", 0b0100: "S", 0b1000: "W",
    0b0101: "NS", 0b0011: "NE", 0b0110: "ES", 0b1100: "SW", 0b1001: "NW",
    0b0111: "NES", 0b1110: "ESW", 0b1101: "NSW", 0b1011: "NEW", 0b1111: "NEWS",
}

# Concrete glyphs for each connector family
TILES: Dict[str, Dict[str, str]] = {
    "light": {
        "SP":" ",  "N":"│","E":"─","S":"│","W":"─",
        "NS":"│","EW":"─",
        "NE":"└","ES":"┌","SW":"┐","NW":"┘",
        "NES":"├","ESW":"┬","NSW":"┤","NEW":"┴","NEWS":"┼",
    },
    "heavy": {
        "SP":" ",  "N":"┃","E":"━","S":"┃","W":"━",
        "NS":"┃","EW":"━",
        "NE":"┗","ES":"┏","SW":"┓","NW":"┛",
        "NES":"┣","ESW":"┳","NSW":"┫","NEW":"┻","NEWS":"╋",
    },
    "double": {
        "SP":" ",  "N":"║","E":"═","S":"║","W":"═",
        "NS":"║","EW":"═",
        "NE":"╚","ES":"╔","SW":"╗","NW":"╝",
        "NES":"╠","ESW":"╦","NSW":"╣","NEW":"╩","NEWS":"╬",
    },
    "rounded": {
        "SP":" ",  "N":"│","E":"─","S":"│","W":"─",
        "NS":"│","EW":"─",
        "NE":"╰","ES":"╭","SW":"╮","NW":"╯",
        "NES":"├","ESW":"┬","NSW":"┤","NEW":"┴","NEWS":"┼",
    },
    "ascii": {
        "SP":" ",  "N":"|","E":"-","S":"|","W":"-",
        "NS":"|","EW":"-",
        "NE":"`","ES":".","SW":"'","NW":",",
        "NES":"+","ESW":"+","NSW":"+","NEW":"+","NEWS":"+",
    },
}

# ---------- Automaton ----------
def step_rule(bits: List[int], rule: int, burst: float) -> List[int]:
    """1D 3-neighbor CA with Wolfram rule (0..255)."""
    n = len(bits)
    out = [0]*n
    for i in range(n):
        l = bits[(i-1) % n]
        c = bits[i]
        r = bits[(i+1) % n]
        idx = (l<<2) | (c<<1) | r
        out[i] = (rule >> idx) & 1
        if burst > 0.0 and random.random() < burst:
            out[i] ^= 1
    return out

@dataclass
class Cell:
    fg: Tuple[int,int,int]
    bg: Tuple[int,int,int]
    bit: int
    glyph: str

def render_cell(cellw: int, fg: Tuple[int,int,int], bg: Tuple[int,int,int], glyph: str, use_color: bool) -> str:
    pad = cellw - len(glyph)
    if use_color:
        fr, fg_, fb = fg
        br, bg_, bb = bg
        base = f"\x1b[38;2;{fr};{fg_};{fb}m\x1b[48;2;{br};{bg_};{bb}m{glyph}"
        if pad > 0:
            base += f"\x1b[48;2;{br};{bg_};{bb}m" + (" " * pad)
        return base + "\x1b[0m"
    else:
        return glyph + (" " * max(0, pad))

def choose_connector(mask: int, style: str) -> str:
    key = CODES.get(mask, "SP")
    return TILES[style].get(key, " ")

def build_extras(names: Optional[str], custom: Optional[str]) -> List[str]:
    bag: List[str] = []
    if names:
        for name in (n.strip() for n in names.split(",") if n.strip()):
            bag.extend(GLYPH_SETS.get(name, []))
    if custom:
        bag.extend([t for t in custom.split(" ") if t])
    return bag

# ---------- Renderer ----------
class AsciiRenderer:
    def __init__(self,
                 style: str = "light",
                 bg_glyph: Optional[str] = None,
                 bg_set: Optional[str] = None,
                 fg_glyph: Optional[str] = None,
                 extras: Optional[str] = None,
                 custom: Optional[str] = None,
                 extra_prob: float = 0.0,
                 no_color: bool = False):
        self.style = style
        self.bg_glyph = bg_glyph
        self.bg_set = bg_set
        self.fg_glyph = fg_glyph
        self.extra_prob = max(0.0, min(1.0, extra_prob))
        self.use_color = not no_color
        self.extras = build_extras(extras, custom)

        self.cellw = max(1, len(self.bg_glyph) if self.bg_glyph else 1,
                         max((len(t) for t in self.extras), default=1))

        # Precompute a background choice sequence if a set is chosen
        self.bg_cycle = (GLYPH_SETS.get(bg_set, [" "]) if bg_set else [self.bg_glyph or " "])
        if not self.bg_cycle:
            self.bg_cycle = [" "]

    def render_row(self,
                   bits: List[int],
                   prev_bits: List[int],
                   fgs: List[Tuple[int,int,int]],
                   bgs: List[Tuple[int,int,int]]) -> str:
        n = len(bits)
        parts: List[str] = []
        for i in range(n):
            if bits[i] == 0:
                # OFF cell — background glyph from set or chosen glyph
                bglyph = self.bg_cycle[i % len(self.bg_cycle)]
                # occasional sprinkled extras on background
                glyph = (random.choice(self.extras)
                         if (self.extras and random.random() < self.extra_prob)
                         else bglyph * 1)
                parts.append(render_cell(self.cellw, fgs[i], bgs[i], glyph, self.use_color))
                continue

            # ON cell
            if self.fg_glyph:
                glyph = self.fg_glyph
            else:
                up = 1 if prev_bits[i] == 1 else 0
                right = 1 if bits[(i+1) % n] == 1 else 0
                down = 1
                left  = 1 if bits[(i-1) % n] == 1 else 0
                mask = (up*1) | (right*2) | (down*4) | (left*8)
                glyph = choose_connector(mask, self.style)
                # small chance to spice connectors with extras
                if self.extras and random.random() < (self.extra_prob*0.35):
                    glyph = random.choice(self.extras)
            parts.append(render_cell(self.cellw, fgs[i], bgs[i], glyph, self.use_color))
        return "".join(parts)

# ---------- CLI ----------
def main():
    p = argparse.ArgumentParser(description="Modular ASCII/Unicode maze/river renderer")
    p.add_argument("--rows", type=int, default=0, help="Number of rows to render (0 = infinite until Ctrl+C)")
    p.add_argument("--delay", type=float, default=0.0, help="Seconds to sleep between rows")
    p.add_argument("--width", type=int, default=0, help="Override terminal cell width (cells, not chars)")
    p.add_argument("--rule", type=int, default=110, help="Wolfram rule 0..255")
    p.add_argument("--burst", type=float, default=0.0, help="Random bit flips per cell [0..1]")
    p.add_argument("--jitter", type=float, default=0.5, help="Color jitter amount [0..2]")
    p.add_argument("--style", default="light", choices=list(TILES.keys()), help="Connector family")
    p.add_argument("--bg-glyph", default=None, help="Glyph for OFF cells (overridden by --bg-set)")
    p.add_argument("--bg-set", default=None, choices=[None,*GLYPH_SETS.keys()], help="Named set for OFF cells")
    p.add_argument("--fg-glyph", default=None, help="Force a single glyph for ON cells (ignores connectors)")
    p.add_argument("--extras", default=None, help="Comma‑separated named glyph sets to sprinkle")
    p.add_argument("--custom", default=None, help="Space‑separated custom extras, e.g. '◇ ◆ ★ ☆'")
    p.add_argument("--extra-prob", type=float, default=0.0, help="Chance per cell to insert an extra glyph [0..1]")
    p.add_argument("--seed", type=int, default=None, help="RNG seed")
    p.add_argument("--no-color", action="store_true", help="Disable ANSI colors")
    args = p.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    # UTF‑8 stdout if possible
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    # Build renderer
    renderer = AsciiRenderer(
        style=args.style,
        bg_glyph=args.bg_glyph,
        bg_set=args.bg_set,
        fg_glyph=args.fg_glyph,
        extras=args.extras,
        custom=args.custom,
        extra_prob=args.extra_prob,
        no_color=args.no_color,
    )

    # Determine cell width and terminal width
    term_cols = max(1, shutil.get_terminal_size(fallback=(80, 24)).columns)
    cells = (args.width if args.width > 0 else term_cols // renderer.cellw) or 1

    # Initialize automaton and colors
    prev_bits = [random.randint(0,1) for _ in range(cells)]

    def rand_fg_hsv():
        return (random.random(), 0.85, 0.95)

    fgs: List[Tuple[int,int,int]] = []
    bgs: List[Tuple[int,int,int]] = []
    for _ in range(cells):
        h,s,v = rand_fg_hsv()
        frgb, brgb = anti_colors_from_fg(h, s, v)
        fgs.append(frgb); bgs.append(brgb)

    count = 0
    line_idx = 0
    try:
        while True:
            bits = step_rule(prev_bits, args.rule, args.burst)

            # fresh vivid foregrounds with anti background; slight drift across columns
            fgs2: List[Tuple[int,int,int]] = []
            bgs2: List[Tuple[int,int,int]] = []
            for i in range(cells):
                # mix current fg HSV with two neighbors for gentle hue flow
                def rgb_to_hsv(r,g,b):
                    # quick & dirty inverse for drift; good enough for jitter
                    mx, mn = max(r,g,b)/255.0, min(r,g,b)/255.0
                    v = mx
                    d = (mx - mn) or 1e-9
                    s = 0.0 if mx == 0 else d/mx
                    if d == 0: h = 0.0
                    elif mx == r/255.0: h = ((g-b)/255.0)/d % 6
                    elif mx == g/255.0: h = ((b-r)/255.0)/d + 2
                    else: h = ((r-g)/255.0)/d + 4
                    return (h/6.0, s, v)

                h1,s1,v1 = rgb_to_hsv(*fgs[(i-1) % cells])
                h2,s2,v2 = rgb_to_hsv(*fgs[i])
                h3,s3,v3 = rgb_to_hsv(*fgs[(i+1) % cells])
                h,s,v = hsv_mix([(h1,s1,v1),(h2,s2,v2),(h3,s3,v3)], args.jitter)
                frgb, brgb = anti_colors_from_fg(h, s, v)
                fgs2.append(frgb); bgs2.append(brgb)

            line = renderer.render_row(bits, prev_bits, fgs2, bgs2)
            sys.stdout.write(line + "\n")
            sys.stdout.flush()

            prev_bits = bits
            fgs = fgs2; bgs = bgs2
            line_idx += 1; count += 1
            if args.rows and count >= args.rows:
                break
            if args.delay > 0.0:
                time.sleep(args.delay)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\x1b[0m")
        sys.stdout.flush()

if __name__ == "__main__":
    main()
