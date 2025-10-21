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

def srgb_to_linear(c: float) -> float:
    return c/12.92 if c <= 0.04045 else ((c+0.055)/1.055) ** 2.4

def linear_to_srgb(c: float) -> float:
    return 12.92*c if c <= 0.0031308 else 1.055*(c ** (1/2.4)) - 0.055

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
    return rgb_tuple(r, g, b)

def rgb_to_hsv(r: int, g: int, b: int) -> Tuple[float,float,float]:
    r_, g_, b_ = r/255.0, g/255.0, b/255.0
    mx, mn = max(r_, g_, b_), min(r_, g_, b_)
    d = mx - mn
    v = mx
    s = 0.0 if mx == 0.0 else d/mx
    if d == 0.0:
        h = 0.0
    elif mx == r_:
        h = ((g_ - b_)/d) % 6.0
    elif mx == g_:
        h = ((b_ - r_)/d) + 2.0
    else:
        h = ((r_ - g_)/d) + 4.0
    return (h/6.0, s, v)

def hsl_to_rgb(h: float, s: float, l: float) -> Tuple[int,int,int]:
    def hue2rgb(p, q, t):
        t = t % 1.0
        if t < 1/6: return p + (q-p)*6*t
        if t < 1/2: return q
        if t < 2/3: return p + (q-p)*(2/3 - t)*6
        return p
    if s == 0.0:
        r = g = b = l
    else:
        q = l*(1+s) if l < 0.5 else l + s - l*s
        p = 2*l - q
        r = hue2rgb(p, q, h + 1/3)
        g = hue2rgb(p, q, h)
        b = hue2rgb(p, q, h - 1/3)
    return rgb_tuple(r, g, b)

def rgb_to_hsl(r: int, g: int, b: int) -> Tuple[float,float,float]:
    r_, g_, b_ = r/255.0, g/255.0, b/255.0
    mx, mn = max(r_, g_, b_), min(r_, g_, b_)
    l = (mx + mn)/2.0
    if mx == mn:
        h = s = 0.0
    else:
        d = mx - mn
        s = d / (2.0 - mx - mn) if l > 0.5 else d / (mx + mn)
        if mx == r_:
            h = ((g_ - b_) / d) % 6.0
        elif mx == g_:
            h = ((b_ - r_) / d) + 2.0
        else:
            h = ((r_ - g_) / d) + 4.0
        h /= 6.0
    return (h, s, l)

# ---- OKLab / OKLCh helpers (approximate; no deps) ----
def rgb_to_oklab(r: int, g: int, b: int) -> Tuple[float,float,float]:
    r_lin = srgb_to_linear(r/255.0)
    g_lin = srgb_to_linear(g/255.0)
    b_lin = srgb_to_linear(b/255.0)
    l = 0.4122214708*r_lin + 0.5363325363*g_lin + 0.0514459929*b_lin
    m = 0.2119034982*r_lin + 0.6806995451*g_lin + 0.1073969566*b_lin
    s = 0.0883024619*r_lin + 0.2817188376*g_lin + 0.6299787005*b_lin
    l_, m_, s_ = l**(1/3), m**(1/3), s**(1/3)
    L = 0.2104542553*l_ + 0.7936177850*m_ - 0.0040720468*s_
    a = 1.9779984951*l_ - 2.4285922050*m_ + 0.4505937099*s_
    b = 0.0259040371*l_ + 0.7827717662*m_ - 0.8086757660*s_
    return (L, a, b)

def oklab_to_rgb(L: float, a: float, b: float) -> Tuple[int,int,int]:
    l_ = L + 0.3963377774*a + 0.2158037573*b
    m_ = L - 0.1055613458*a - 0.0638541728*b
    s_ = L - 0.0894841775*a - 1.2914855480*b
    l = l_**3; m = m_**3; s = s_**3
    r_lin = +4.0767416621*l - 3.3077115913*m + 0.2309699292*s
    g_lin = -1.2684380046*l + 2.6097574011*m - 0.3413193965*s
    b_lin = -0.0041960863*l - 0.7034186147*m + 1.7076147010*s
    r = clamp01(linear_to_srgb(r_lin))
    g = clamp01(linear_to_srgb(g_lin))
    b = clamp01(linear_to_srgb(b_lin))
    return (int(round(r*255)), int(round(g*255)), int(round(b*255)))

def oklab_to_oklch(L: float, a: float, b: float) -> Tuple[float,float,float]:
    C = math.hypot(a, b)
    h = (math.degrees(math.atan2(b, a)) % 360.0) / 360.0
    return (L, C, h)

def oklch_to_oklab(L: float, C: float, h: float) -> Tuple[float,float,float]:
    angle = math.radians(h*360.0)
    a = C * math.cos(angle)
    b = C * math.sin(angle)
    return (L, a, b)

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

# ---------- Color Engine ----------
def parse_hex_color(s: str) -> Tuple[int,int,int]:
    s = s.strip().lstrip("#")
    if len(s) == 3:
        s = "".join(ch*2 for ch in s)
    if len(s) != 6:
        raise ValueError(f"Bad hex color: {s}")
    r = int(s[0:2], 16); g = int(s[2:4], 16); b = int(s[4:6], 16)
    return (r,g,b)

def lerp(a: float, b: float, t: float) -> float:
    return a + (b-a)*t

def blend_rgb(c1, c2, t: float) -> Tuple[int,int,int]:
    r = int(round(lerp(c1[0], c2[0], t)))
    g = int(round(lerp(c1[1], c2[1], t)))
    b = int(round(lerp(c1[2], c2[2], t)))
    return (r,g,b)

def blend_hsv(c1, c2, t: float) -> Tuple[int,int,int]:
    h1,s1,v1 = rgb_to_hsv(*c1); h2,s2,v2 = rgb_to_hsv(*c2)
    # shortest arc blend
    dh = ((h2 - h1 + 0.5) % 1.0) - 0.5
    h = (h1 + dh*t) % 1.0
    s = lerp(s1, s2, t)
    v = lerp(v1, v2, t)
    return hsv_to_rgb(h, s, v)

def blend_hsl(c1, c2, t: float) -> Tuple[int,int,int]:
    h1,s1,l1 = rgb_to_hsl(*c1); h2,s2,l2 = rgb_to_hsl(*c2)
    dh = ((h2 - h1 + 0.5) % 1.0) - 0.5
    h = (h1 + dh*t) % 1.0
    s = lerp(s1, s2, t)
    l = lerp(l1, l2, t)
    return hsl_to_rgb(h, s, l)

def blend_oklab(c1, c2, t: float) -> Tuple[int,int,int]:
    L1,a1,b1 = rgb_to_oklab(*c1); L2,a2,b2 = rgb_to_oklab(*c2)
    L = lerp(L1, L2, t); a = lerp(a1, a2, t); b = lerp(b1, b2, t)
    return oklab_to_rgb(L, a, b)

def sample_stops(stops: List[Tuple[int,int,int]], p: float, mode: str) -> Tuple[int,int,int]:
    if not stops:
        return (255,255,255)
    if len(stops) == 1:
        return stops[0]
    p = p % 1.0
    seg = (len(stops) - 1) * p
    i = int(math.floor(seg))
    t = seg - i
    c1 = stops[i]
    c2 = stops[(i+1) % len(stops)]
    if mode == "rgb":
        return blend_rgb(c1, c2, t)
    elif mode == "hsl":
        return blend_hsl(c1, c2, t)
    elif mode == "oklab":
        return blend_oklab(c1, c2, t)
    else:
        return blend_hsv(c1, c2, t)

@dataclass
class ColorConfig:
    scheme: str = "triad"           # complement|analogous|triad|tetrad|split|monochrome|warm|cool|rainbow|custom
    blend: str = "hsv"              # hsv|hsl|rgb|oklab
    pairing: str = "opposite"       # opposite|adjacent|none
    base_hue: Optional[float] = None
    jitter: float = 0.5
    gradient: str = "xt"            # x|t|xt
    scale: float = 1.0              # bigger = slower gradient
    stops: Optional[List[Tuple[int,int,int]]] = None
    bg_gain: float = -0.15          # negative to darken bg, positive to lighten

class ColorEngine:
    def __init__(self, cfg: ColorConfig, width: int, seed: Optional[int] = None):
        self.cfg = cfg
        self.w = max(1, width)
        self.ticks = 0
        if seed is not None:
            random.seed(seed)
        self.base_h = cfg.base_hue if (cfg.base_hue is not None) else random.random()
        self.stops = self._build_stops()

    def _build_stops(self) -> List[Tuple[int,int,int]]:
        if self.cfg.stops:
            return self.cfg.stops
        h = self.base_h
        def hv(hh, s=0.9, v=0.95): return hsv_to_rgb(hh%1.0, s, v)
        sch = self.cfg.scheme
        if sch == "complement":
            return [hv(h), hv(h+0.5)]
        if sch == "analogous":
            return [hv(h-0.06), hv(h), hv(h+0.06)]
        if sch == "split":
            return [hv(h), hv(h+0.45), hv(h-0.45)]
        if sch == "triad":
            return [hv(h), hv(h+1/3), hv(h+2/3)]
        if sch == "tetrad":
            return [hv(h), hv(h+0.25), hv(h+0.5), hv(h+0.75)]
        if sch == "monochrome":
            base = hsv_to_rgb(h, 0.85, 0.95)
            dark = hsv_to_rgb(h, 0.85, 0.35)
            return [dark, base]
        if sch == "warm":
            return [parse_hex_color(c) for c in ["#FF6B6B","#FFC46B","#FFD56B","#FF8E6B"]]
        if sch == "cool":
            return [parse_hex_color(c) for c in ["#69D2FF","#6BC1FF","#6B92FF","#86A8FF"]]
        # rainbow default
        return [hsv_to_rgb(i/6.0, 0.95, 0.95) for i in range(6)]

    def _jitter_rgb(self, c: Tuple[int,int,int]) -> Tuple[int,int,int]:
        j = self.cfg.jitter
        if j <= 0: return c
        h,s,v = rgb_to_hsv(*c)
        h = (h + random.uniform(-0.03*j, 0.03*j)) % 1.0
        s = clamp01(s + random.uniform(-0.04*j, 0.04*j))
        v = clamp01(v + random.uniform(-0.03*j, 0.03*j))
        return hsv_to_rgb(h, s, v)

    def _pair_bg(self, fg: Tuple[int,int,int]) -> Tuple[int,int,int]:
        if self.cfg.pairing == "none":
            # same hue, dimmed
            h,s,v = rgb_to_hsv(*fg)
            v = clamp01(v + self.cfg.bg_gain)
            return hsv_to_rgb(h, s, v)
        if self.cfg.blend in ("hsv","hsl"):
            h,s,v = rgb_to_hsv(*fg) if self.cfg.blend=="hsv" else rgb_to_hsl(*fg)
            if self.cfg.pairing == "adjacent":
                h = (h + 1/12) % 1.0  # +30deg
            else:  # opposite
                h = (h + 0.5) % 1.0
            if self.cfg.blend=="hsv":
                return hsv_to_rgb(h, s, clamp01(v + self.cfg.bg_gain))
            else:
                return hsl_to_rgb(h, s, clamp01(v + self.cfg.bg_gain*0.6))
        # oklab/rgb paths: convert to oklab, shift hue via oklch
        L,a,b = rgb_to_oklab(*fg)
        L,C,h = oklab_to_oklch(L,a,b)
        if self.cfg.pairing == "adjacent":
            h = (h + 30/360.0) % 1.0
        else:
            h = (h + 0.5) % 1.0
        L = clamp01(L + self.cfg.bg_gain*0.4)
        L2,a2,b2 = oklch_to_oklab(L, C, h)
        return oklab_to_rgb(L2, a2, b2)

    def _position(self, x: int) -> float:
        sc = max(1e-6, self.cfg.scale)
        if self.cfg.gradient == "x":
            return (x / self.w) / sc
        if self.cfg.gradient == "t":
            return (self.ticks / (100.0*sc))
        return ((x / self.w) + (self.ticks / (100.0*sc)))

    def next_row_colors(self, width: int) -> Tuple[List[Tuple[int,int,int]], List[Tuple[int,int,int]]]:
        fgs: List[Tuple[int,int,int]] = []
        bgs: List[Tuple[int,int,int]] = []
        for i in range(width):
            p = self._position(i)
            fg = self._jitter_rgb(sample_stops(self.stops, p, self.cfg.blend))
            bg = self._pair_bg(fg)
            fgs.append(fg); bgs.append(bg)
        self.ticks += 1
        return fgs, bgs

# ---------- Cells ----------
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
                 no_color: bool = False,
                 layer_mode: str = "flat"):
        self.style = style
        self.bg_glyph = bg_glyph
        self.bg_set = bg_set
        self.fg_glyph = fg_glyph
        self.extra_prob = max(0.0, min(1.0, extra_prob))
        self.use_color = not no_color
        self.layer_mode = layer_mode  # flat | duotone
        self.extras = build_extras(extras, custom)

        self.cellw = max(1, len(self.bg_glyph) if self.bg_glyph else 1,
                         len(self.fg_glyph) if self.fg_glyph else 1,
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
            if self.layer_mode == "duotone":
                # Use upper half block so foreground ink sits on top, bg shows below
                glyph = "▀" if bits[i] == 1 else "▀"
                parts.append(render_cell(self.cellw, fgs[i], bgs[i], glyph, self.use_color))
                continue

            if bits[i] == 0:
                # OFF cell — background glyph from set or chosen glyph
                bglyph = self.bg_cycle[i % len(self.bg_cycle)]
                # occasional sprinkled extras on background
                glyph = (random.choice(self.extras)
                         if (self.extras and random.random() < self.extra_prob)
                         else bglyph * 1)
                parts.append(render_cell(self.cellw, fgs[i], bgs[i], glyph, self.use_color))
                continue

            # ON cell (flat mode)
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
    p.add_argument("--style", default="light", choices=list(TILES.keys()), help="Connector family")
    p.add_argument("--bg-glyph", default=None, help="Glyph for OFF cells (overridden by --bg-set)")
    p.add_argument("--bg-set", default=None, choices=[None,*GLYPH_SETS.keys()], help="Named set for OFF cells")
    p.add_argument("--fg-glyph", default=None, help="Force a single glyph for ON cells (ignores connectors)")
    p.add_argument("--extras", default=None, help="Comma‑separated named glyph sets to sprinkle")
    p.add_argument("--custom", default=None, help="Space‑separated custom extras, e.g. '◇ ◆ ★ ☆'")
    p.add_argument("--extra-prob", type=float, default=0.0, help="Chance per cell to insert an extra glyph [0..1]")
    p.add_argument("--seed", type=int, default=None, help="RNG seed")
    p.add_argument("--no-color", action="store_true", help="Disable ANSI colors")

    # color engine options
    p.add_argument("--color-scheme", default="triad",
                   choices=["complement","analogous","triad","tetrad","split","monochrome","warm","cool","rainbow","custom"],
                   help="High‑level palette arrangement")
    p.add_argument("--blend", default="hsv", choices=["hsv","hsl","rgb","oklab"], help="Space for gradient blending")
    p.add_argument("--pairing", default="opposite", choices=["opposite","adjacent","none"], help="Background color relation to foreground")
    p.add_argument("--stops", default=None, help="Comma‑separated hex stops for --color-scheme custom, e.g. '#ff0088,#00ffaa,#223344'")
    p.add_argument("--base-hue", type=float, default=None, help="Base hue in [0..1]; if omitted a random base is used")
    p.add_argument("--jitter", type=float, default=0.5, help="Color jitter amount [0..2]")
    p.add_argument("--gradient", default="xt", choices=["x","t","xt"], help="Gradient direction: across columns, over time, or both")
    p.add_argument("--scale", type=float, default=1.0, help="Gradient scale (bigger = slower change)")
    p.add_argument("--bg-gain", type=float, default=-0.15, help="Brightness tweak for background pairing (-1..+1)")

    # layer
    p.add_argument("--layer-mode", default="flat", choices=["flat","duotone"],
                   help="flat=normal glyphs; duotone=upper‑half block with fg over bg (overlay‑ish)")

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
        layer_mode=args.layer_mode,
    )

    # Determine cell width and terminal width
    term_cols = max(1, shutil.get_terminal_size(fallback=(80, 24)).columns)
    cells = (args.width if args.width > 0 else term_cols // renderer.cellw) or 1

    # Initialize automaton and colors
    prev_bits = [random.randint(0,1) for _ in range(cells)]

    # Color engine
    stops_list = None
    if args.stops:
        try:
            stops_list = [parse_hex_color(s) for s in args.stops.split(",") if s.strip()]
        except Exception as e:
            print(f"[warn] could not parse --stops: {e}", file=sys.stderr)

    cfg = ColorConfig(
        scheme=args.color_scheme,
        blend=args.blend,
        pairing=args.pairing,
        base_hue=args.base_hue,
        jitter=args.jitter,
        gradient=args.gradient,
        scale=args.scale,
        stops=stops_list,
        bg_gain=args.bg_gain,
    )
    cengine = ColorEngine(cfg, width=cells, seed=args.seed)

    count = 0
    line_idx = 0
    try:
        while True:
            bits = step_rule(prev_bits, args.rule, args.burst)
            fgs, bgs = cengine.next_row_colors(cells)

            line = renderer.render_row(bits, prev_bits, fgs, bgs)
            sys.stdout.write(line + "\n")
            sys.stdout.flush()

            prev_bits = bits
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
