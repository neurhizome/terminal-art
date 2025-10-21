#!/usr/bin/env python3
# maze_river.py
#
# Dusty's maze river: terminal-width aware, 24-bit color, connector tiles that actually join,
# optional multi-char glyphs, anti-colors for vivid contrast, and a 1D→2D-ish cellular automaton
# that drives emergent corridors. No external deps.
#
# Examples:
#   python3 maze_river.py --rows 1000 --delay 0.01
#   python3 maze_river.py --rule 110 --style heavy --extras pipes,angles --extra_prob 0.07
#   python3 maze_river.py --style rotate --extras digraphs --extra_prob 0.15
#   python3 maze_river.py --style double --seed 23 --jitter 1.0
#
# Notes:
# - "style" picks the connector family used to assemble mazes: light/heavy/double/rounded/rotate.
# - "extras" lets you sprinkle thin pipes, angles, blocks, braille, ascii, or digraphs, or pass your
#   own string via --custom "── ╱╲ ░░".
# - Multi-char tiles are padded so each cell consumes a fixed width; the background color fills the pad.
# - CA is elementary (0..255). Default 110 for nice complexity. It computes the next row's "on/off"
#   states from the previous row; connectors are chosen to link left/right and to the row above.

import argparse
import random
import shutil
import sys
import time
import math
import colorsys
from dataclasses import dataclass
from typing import List, Tuple, Dict

# ----------------------------- Tiles & Packs -----------------------------

# Canonical connector codes by (N,E,S,W) bitmask -> symbolic key
# bits: N=1, E=2, S=4, W=8
CODES = {
    0b0000: "SP",
    0b0001: "N",
    0b0010: "E",
    0b0100: "S",
    0b1000: "W",
    0b0101: "NS",
    0b1010: "EW",
    0b0011: "NE",
    0b0110: "ES",
    0b1100: "SW",
    0b1001: "NW",
    0b0111: "NES",
    0b1110: "ESW",
    0b1101: "NSW",
    0b1011: "NEW",
    0b1111: "NEWS",
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
    # Rounded has fewer true connectors; we approximate corners
    "rounded": {
        "SP":" ",  "N":"│","E":"─","S":"│","W":"─",
        "NS":"│","EW":"─",
        "NE":"╰","ES":"╭","SW":"╮","NW":"╯",
        "NES":"├","ESW":"┬","NSW":"┤","NEW":"┴","NEWS":"┼",
    },
}

# Optional extra packs for texture; mixed in with probability
EXTRAS: Dict[str, List[str]] = {
    "pipes":  list("╶╴╷╵╺╻╼╽┄┆┈┊"),
    "angles": list("╱╲╳"),
    "blocks": list("▘▝▖▗▚▞▌▐▀▁▏▎▍▌▋▊▉█"),
    "ascii":  list("-|+/\\"),
    "braille": list("⢀⡀⠄⠂⠁⠈⠐⠠⡠⣀⣤⣿"),
    "digraphs": ["──","━━","██","░░","▒▒","▓▓","╱╱","╲╲","╳╳","╴╶","╷╵"],
}

def pick_style(style_name: str, line_index: int) -> str:
    if style_name != "rotate":
        return style_name
    order = ["light","heavy","double","rounded"]
    return order[line_index % len(order)]

# ----------------------------- Color helpers -----------------------------

def clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)

def clamp8(x: float) -> int:
    x = 0 if x < 0 else (255 if x > 255 else x)
    return int(x)

def rgb_tuple(r: float, g: float, b: float) -> Tuple[int,int,int]:
    return (clamp8(r*255), clamp8(g*255), clamp8(b*255))

def hsv_mix(hsvs: List[Tuple[float,float,float]], jitter: float) -> Tuple[float,float,float]:
    # Random symmetric weights (Dirichlet(1,1,...)
    ws = [random.random() for _ in hsvs]
    s = sum(ws) or 1.0
    ws = [w/s for w in ws]
    # Circular hue mean
    xs = sum(w*math.cos(2*math.pi*h) for (w,(h,_,_)) in zip(ws, hsvs))
    ys = sum(w*math.sin(2*math.pi*h) for (w,(h,_,_)) in zip(ws, hsvs))
    h = (math.atan2(ys, xs) / (2*math.pi)) % 1.0
    s_ = sum(w*sv for w,(_,sv,_) in zip(ws, hsvs))
    v_ = sum(w*vv for w,(_,_,vv) in zip(ws, hsvs))
    # Anti-fade: lean toward max V and nudge S up
    vmax = max(v for _,_,v in hsvs)
    v = 0.80*vmax + 0.20*v_
    s = clamp01(s_*1.08)
    # Small jitter
    h = (h + random.uniform(-0.03*jitter, 0.03*jitter)) % 1.0
    s = clamp01(s + random.uniform(-0.04*jitter, 0.04*jitter))
    v = clamp01(v + random.uniform(-0.04*jitter, 0.04*jitter))
    return h, s, v

def anti_colors_from_fg(h: float, s: float, v: float) -> Tuple[Tuple[int,int,int], Tuple[int,int,int]]:
    # Given desired FG HSV, create BG as a vibrant anti-color: complementary hue and inverted value.
    fg_h, fg_s, fg_v = h % 1.0, clamp01(s), clamp01(v)
    bg_h = (fg_h + 0.5) % 1.0
    # Keep both punchy
    fg_s = clamp01(0.35 + 0.65*fg_s)
    bg_s = clamp01(0.45 + 0.55*(1.0 - fg_s))
    bg_v = clamp01(0.60 + 0.40*(1.0 - fg_v))  # if fg is dark, bg becomes light; if fg is bright, bg dims a bit
    rf, gf, bf = colorsys.hsv_to_rgb(fg_h, fg_s, fg_v)
    rb, gb, bb = colorsys.hsv_to_rgb(bg_h, bg_s, bg_v)
    return rgb_tuple(rf,gf,bf), rgb_tuple(rb,gb,bb)

# ----------------------------- Cellular Automaton -----------------------------

def next_state_row(prev_bits: List[int], rule: int, burst: float) -> List[int]:
    n = len(prev_bits)
    out = [0]*n
    for i in range(n):
        l = prev_bits[(i-1) % n]
        c = prev_bits[i]
        r = prev_bits[(i+1) % n]
        idx = (l<<2) | (c<<1) | r
        out[i] = (rule >> idx) & 1
        if burst > 0.0 and random.random() < burst:
            out[i] ^= 1  # occasional spark to keep things lively
    return out

# ----------------------------- Rendering Model -----------------------------

@dataclass
class Cell:
    fg: Tuple[int,int,int]
    bg: Tuple[int,int,int]
    bit: int  # CA state
    tile: str # rendered glyph

def choose_connector(mask: int, style: str) -> str:
    key = CODES.get(mask, "SP")
    return TILES[style].get(key, " ")

def render_cell(cellw: int, fg: Tuple[int,int,int], bg: Tuple[int,int,int], glyph: str) -> str:
    # Pad glyph to fixed width; fill background under padding for clean blocks.
    pad = cellw - len(glyph)
    fr, fg_, fb = fg
    br, bg_, bb = bg
    base = f"\x1b[38;2;{fr};{fg_};{fb}m\x1b[48;2;{br};{bg_};{bb}m{glyph}"
    if pad > 0:
        base += f"\x1b[48;2;{br};{bg_};{bb}m" + (" " * pad)
    return base + "\x1b[0m"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", type=int, default=0, help="0 = infinite")
    ap.add_argument("--delay", type=float, default=0.02, help="seconds between lines")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--style", default="heavy", choices=["light","heavy","double","rounded","rotate"])
    ap.add_argument("--extras", default="", help="comma list: pipes,angles,blocks,ascii,braille,digraphs")
    ap.add_argument("--custom", default="", help="space-separated custom tiles, e.g. '── ╱╲ ░░'")
    ap.add_argument("--extra_prob", type=float, default=0.08, help="chance to drop an extra tile in a cell")
    ap.add_argument("--rule", type=int, default=110, help="elementary CA rule 0..255")
    ap.add_argument("--burst", type=float, default=0.02, help="random flip probability per cell")
    ap.add_argument("--hsv_jitter", type=float, default=1.0, help="color jitter multiplier (0..2)")
    args = ap.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    # UTF-8 just in case
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    # Build the extra tile bag
    extra_bag: List[str] = []
    if args.extras:
        for name in (n.strip() for n in args.extras.split(",") if n.strip()):
            extra_bag.extend(EXTRAS.get(name, []))
    if args.custom:
        extra_bag.extend([t for t in args.custom.split(" ") if t])

    # Fixed cell width = max(1, longest tile among connectors & extras)
    # Connector tiles are all 1 char; extras may be multi-char.
    longest_extra = max((len(t) for t in extra_bag), default=1)
    cellw = max(1, longest_extra)

    # Determine initial width in cells (not chars)
    term_cols = max(1, shutil.get_terminal_size(fallback=(80, 24)).columns)
    cells = max(1, term_cols // cellw)

    # Initial bits/colors: random noise
    prev_bits = [random.randint(0,1) for _ in range(cells)]
    # Random vivid FG as seed; BG will be set anti to FG during render
    def rand_fg():
        h = random.random()
        s = 0.65 + 0.35*random.random()
        v = 0.55 + 0.45*random.random()
        rf,gf,bf = colorsys.hsv_to_rgb(h,s,v)
        return rgb_tuple(rf,gf,bf)
    prev_fg = [rand_fg() for _ in range(cells)]
    prev_bg = [anti_colors_from_fg(
                    colorsys.rgb_to_hsv(*(c/255 for c in f))[0],
                    colorsys.rgb_to_hsv(*(c/255 for c in f))[1],
                    colorsys.rgb_to_hsv(*(c/255 for c in f))[2])[1]
               for f in prev_fg]

    line_idx = 0
    count = 0
    try:
        while True:
            # Track terminal width and recompute cell count if needed
            new_cols = max(1, shutil.get_terminal_size(fallback=(80, 24)).columns)
            if new_cols != term_cols:
                term_cols = new_cols
                cells = max(1, term_cols // cellw)
                # resize state arrays
                prev_bits = (prev_bits[:cells] + [random.randint(0,1) for _ in range(max(0, cells-len(prev_bits)))])[:cells]
                prev_fg   = (prev_fg[:cells]   + [rand_fg() for _ in range(max(0, cells-len(prev_fg)))])[:cells]
                prev_bg   = (prev_bg[:cells]   + [ (0,0,0) for _ in range(max(0, cells-len(prev_bg)))])[:cells]

            # Compute next CA row
            bits = next_state_row(prev_bits, rule=args.rule & 255, burst=args.burst)

            # Merge colors from neighbors (HSV anti-fade), then build FG/BG pair as anti-colors
            fgs: List[Tuple[int,int,int]] = []
            bgs: List[Tuple[int,int,int]] = []
            for i in range(cells):
                left = prev_fg[(i-1) % cells]
                selfc = prev_fg[i]
                right = prev_fg[(i+1) % cells]
                hsvs = [colorsys.rgb_to_hsv(*(c/255 for c in left)),
                        colorsys.rgb_to_hsv(*(c/255 for c in selfc)),
                        colorsys.rgb_to_hsv(*(c/255 for c in right))]
                h,s,v = hsv_mix(hsvs, jitter=args.hsv_jitter)
                # Punch color a bit if a new "on" is born here
                if bits[i] == 1 and prev_bits[i] == 0:
                    s = clamp01(s*1.15); v = clamp01(0.85*v + 0.15)
                fg, bg = anti_colors_from_fg(h, s, v)
                fgs.append(fg); bgs.append(bg)

            # Build connector masks using current row + link to the row above
            style = pick_style(args.style, line_idx)
            line_parts: List[str] = []
            for i in range(cells):
                if bits[i] == 0:
                    # off cell: occasionally drop an extra texture tile, otherwise just a faint spacer
                    if extra_bag and random.random() < args.extra_prob:
                        glyph = random.choice(extra_bag)
                    else:
                        glyph = " " * cellw
                    line_parts.append(render_cell(cellw, fgs[i], bgs[i], glyph))
                    continue

                # This cell is "on": connect to neighbors
                up = 1 if prev_bits[i] == 1 else 0
                right = 1 if bits[(i+1) % cells] == 1 else 0
                down = 1  # extend hope downward; next row may or may not connect up
                left = 1 if bits[(i-1) % cells] == 1 else 0
                mask = (up*1) | (right*2) | (down*4) | (left*8)
                glyph = choose_connector(mask, style)

                # occasional spice: replace wwith an extra glyph but keep connectors the majority of the time
                if extra_bag and random.random() < (args.extra_prob*0.35):
                    glyph = random.choice(extra_bag)

                line_parts.append(render_cell(cellw, fgs[i], bgs[i], glyph))

            sys.stdout.write("".join(line_parts) + "\n")
            sys.stdout.flush()

            # prepare next loop
            prev_bits = bits
            prev_fg   = fgs
            prev_bg   = bgs
            line_idx += 1
            count += 1
            if args.rows and count >= args.rows:
                break
            if args.delay > 0:
                time.sleep(args.delay)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\x1b[0m")
        sys.stdout.flush()

if __name__ == "__main__":
    main()
