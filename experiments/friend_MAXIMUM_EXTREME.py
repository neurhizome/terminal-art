#!/usr/bin/env python3
"""
friend_MAXIMUM_EXTREME.py — evolved from Dusty's friend.py, by Opus 4.6.

A terminal cellular automaton where each cell is a Dot with foreground/background
RGB values that evolve through neighbor-blending with tunable "distort" divisors.

THE INFLATION FACTOR
--------------------
For a homogeneous field (all neighbors equal), the gain per step is:

    gain = (1 + 4/avg_div) / blend_div

At exact values (4.0, 2.0): gain = 1.000  →  no drift, gray death.

Modes with gain > 1.0 cause integer values to GROW, and the % 256 display
wrapping creates color phase oscillation patterns. The _blend operation is
identical for evolve and devolve — only the divisor pair differs.

    mode          e_gain    d_gain    net/cycle    after 40 cycles
    original       1.039     0.995      1.034         3.83×
    sine           1.447     0.930      1.345    142,694×   ← insane
    golden         1.139     0.929      1.058         9.46×
    monstertruck   1.146     1.053      1.206      1782×    ← both phases grow
    breathing   oscillates between growth and decay
    critical       1.023     0.984      1.007         1.30×  ← knife-edge slow

Note: the monstertruck devolve also AMPLIFIES (gain 1.053 > 1.0), so neither
phase collapses — the piece just cycles at different speeds.

GLYPHS
------
Each Dot draws its glyph from a pool, and the glyph is updated every step
using a color hash: position in pool = (step + Σ color channels) % pool_size.
The glyph becomes a fingerprint of the cell's color history.

Run from repo root:
  python3 experiments/friend_MAXIMUM_EXTREME.py
  python3 experiments/friend_MAXIMUM_EXTREME.py 80 --mode monstertruck --glyphs kanji
  python3 experiments/friend_MAXIMUM_EXTREME.py 120 --mode critical --glyphs rune
  python3 experiments/friend_MAXIMUM_EXTREME.py --info --mode sine
  python3 experiments/friend_MAXIMUM_EXTREME.py 60 --mode golden --glyphs math --capture museum/golden-math.ans
"""

from random import randint, choice
import math
import os
import sys
import time
import argparse
from contextlib import contextmanager
from pathlib import Path

# ---------------------------------------------------------------------------
# Glyph sets
# ---------------------------------------------------------------------------

GLYPH_SETS = {
    "block":   list("▤▥▦▧▨▩▣▢░▒▓█"),
    "braille": [chr(c) for c in range(0x2800, 0x28FF + 1) if c % 7 in (0, 1, 3, 5)],
    "rune":    list("ᚠᚢᚦᚨᚱᚲᚷᚹᚺᚻᚾᛁᛃᛇᛈᛉᛊᛏᛒᛖᛗᛚᛜᛝᛞᛟ"),
    "kanji":   list("道気空風火水雷山地天星月光影夢幻"),
    "math":    list("∀∃∄∅∆∇∈∉∊∋∌∍∎∏∐∑√∛∜∝∞∟∠∡∢∣"),
    "chaos":   list("◈◉◊○◌◍◎●◐◑◒◓◔◕◖◗◘◙◚◛◜◝◞◟"),
    "ascii":   list("@#$%&*+=~^|<>?!{}[]()/:;"),
}

# ---------------------------------------------------------------------------
# Distort modes
# ---------------------------------------------------------------------------

def get_distort_params(mode: str, step: int, total_steps: int) -> tuple:
    """
    Returns (evolve_avg_div, evolve_blend_div, devolve_avg_div, devolve_blend_div).

    Actual per-step gain (homogeneous field) = (1 + 4/avg_div) / blend_div.
    Values > 1.0 grow; values wrap at display time via % 256.
    """
    t = step / max(total_steps, 1)   # normalized time 0→1
    phi = (1.0 + math.sqrt(5)) / 2

    if mode == "original":
        # Dusty's magic numbers.
        # Evolve gain 1.039, devolve 0.995, net/cycle +3.4%
        return (3.759, 1.986, 4.008, 2.008)

    elif mode == "sine":
        # π-based divisors.
        # Evolve gain 1.447/step → 142,694× after 40 cycles.
        # Devolve still slightly damps (0.930) but evolve dominates wildly.
        return (3.141, 1.571, 4.200, 2.100)

    elif mode == "golden":
        # φ-based. Evolve gain 1.139, net/cycle +5.8%.
        # Organic spiraling — two incommensurate irrationals in the divisors.
        return (2 * phi + 0.5, phi + 0.2, 2 * phi + 0.9, phi + 0.5)
        # ≈ (3.736, 1.818, 4.136, 2.118)

    elif mode == "quantum":
        # Divisors oscillate each step — shimmer and interference patterns.
        wobble  = math.sin(step * 0.3) * 0.15
        dwobble = math.cos(step * 0.3) * 0.12
        return (3.759 + wobble, 1.986 + wobble * 0.5,
                4.008 + dwobble, 2.008 + dwobble * 0.5)

    elif mode == "monstertruck":
        # Both phases AMPLIFY. Evolve 1.146, devolve 1.053 — net +20.6%/cycle.
        # Values cycle through 0-255 roughly 1,782× in 40 cycles.
        return (3.400, 1.900, 3.800, 1.950)

    elif mode == "breathing":
        # Smooth oscillation — the piece pulses between growth and decay.
        # 4 full breath cycles across the entire run.
        breath = math.sin(t * math.pi * 4) * 0.3
        avg_d  = 3.759 - breath
        bld_d  = 1.986 - breath * 0.3
        return (avg_d, bld_d, avg_d + 0.3, bld_d + 0.1)

    elif mode == "critical":
        # Knife-edge: net gain +0.66%/cycle → only 1.30× after 40 cycles.
        # Values grow so slowly that spatial patterns have time to crystallize
        # before the mod-256 wrap erases them. Long smooth gradients.
        return (3.920, 1.975, 4.050, 2.020)

    else:
        return (3.759, 1.986, 4.008, 2.008)


def describe_mode(mode: str, cycles: int) -> None:
    """Print mode parameters and predicted behavior."""
    e_avg, e_bld, d_avg, d_bld = get_distort_params(mode, 0, cycles * 2)
    eg  = (1 + 4 / e_avg) / e_bld
    dg  = (1 + 4 / d_avg) / d_bld
    net = eg * dg
    print(f"mode: {mode}")
    print(f"  evolve:  avg_div={e_avg:.4f}  blend_div={e_bld:.4f}  gain={eg:.5f}/step")
    print(f"  devolve: avg_div={d_avg:.4f}  blend_div={d_bld:.4f}  gain={dg:.5f}/step")
    print(f"  net/cycle: {net:.6f}   after {cycles} cycles: {net**cycles:.2f}×")
    if mode in ("quantum", "breathing"):
        print(f"  note: {mode} mode has dynamic divisors; values shown for step 0")


# ---------------------------------------------------------------------------
# Dot
# ---------------------------------------------------------------------------

class Dot:

    __slots__ = ("idx", "fr", "fg", "fb", "br", "bg", "bb",
                 "glyph", "glyph_pool", "ldot_idx", "rdot_idx", "opp_idx")

    def __init__(self, idx: int, glyph_set: str = "block"):
        self.idx  = idx
        self.fr   = randint(0, 255)
        self.fg   = randint(0, 255)
        self.fb   = randint(0, 255)
        self.br   = randint(0, 255)
        self.bg   = randint(0, 255)
        self.bb   = randint(0, 255)
        self.glyph_pool = GLYPH_SETS.get(glyph_set, GLYPH_SETS["block"])
        self.glyph      = choice(self.glyph_pool)
        self.ldot_idx: int = 0
        self.rdot_idx: int = 0
        self.opp_idx:  int = 0

    def get_str(self) -> str:
        return (
            f"\x1b[38;2;{self.fr % 256};{self.fg % 256};{self.fb % 256}m"
            f"\x1b[48;2;{self.br % 256};{self.bg % 256};{self.bb % 256}m"
            f"{self.glyph}\x1b[0m"
        )

    def evolve_glyph(self, step: int) -> None:
        """Glyph tracks color history — deterministic fingerprint of cell state."""
        h = (self.fr + self.fg * 3 + self.fb * 7
             + self.br * 11 + self.bg * 13 + self.bb * 17 + step)
        self.glyph = self.glyph_pool[h % len(self.glyph_pool)]

    def _blend(self, ldot: "Dot", rdot: "Dot", opp: "Dot",
               avg_div: float, blend_div: float) -> None:
        """
        Core blend operation shared by evolve and devolve.

        The fg↔bg crossover with opp is the soul of the piece:
        self's foreground averages with opp's BACKGROUND (and vice versa),
        coupling each cell to its mirror's complementary channel.
        """
        ofr, ofg, ofb = self.fr, self.fg, self.fb
        obr, obg, obb = self.br, self.bg, self.bb

        afr = (ofr + ldot.fr + rdot.fr + opp.br) / avg_div
        afg = (ofg + ldot.fg + rdot.fg + opp.bg) / avg_div
        afb = (ofb + ldot.fb + rdot.fb + opp.bb) / avg_div
        abr = (obr + ldot.br + rdot.br + opp.fr) / avg_div
        abg = (obg + ldot.bg + rdot.bg + opp.fg) / avg_div
        abb = (obb + ldot.bb + rdot.bb + opp.fb) / avg_div

        self.fr = int((ofr + afr) / blend_div)
        self.fg = int((ofg + afg) / blend_div)
        self.fb = int((ofb + afb) / blend_div)
        self.br = int((obr + abr) / blend_div)
        self.bg = int((obg + abg) / blend_div)
        self.bb = int((obb + abb) / blend_div)

    def evolve_with_neighbors(self, ldot, rdot, opp, avg_div, blend_div):
        self._blend(ldot, rdot, opp, avg_div, blend_div)

    def devolve_with_neighbors(self, ldot, rdot, opp, avg_div, blend_div):
        self._blend(ldot, rdot, opp, avg_div, blend_div)


# ---------------------------------------------------------------------------
# Line
# ---------------------------------------------------------------------------

class Line:

    def __init__(self, glyph_set: str = "block"):
        try:
            self.width = os.get_terminal_size().columns
        except OSError:
            self.width = int(os.environ.get("COLUMNS", 96))
        self.dots: list[Dot] = [Dot(i, glyph_set) for i in range(self.width)]
        for i, d in enumerate(self.dots):
            d.ldot_idx = (i - 1) % self.width
            d.rdot_idx = (i + 1) % self.width
            d.opp_idx  = abs(self.width - 1 - i)

    def _step(self, method: str, avg_div: float, blend_div: float,
              step: int, evolve_glyphs: bool) -> None:
        fn = Dot.evolve_with_neighbors if method == "e" else Dot.devolve_with_neighbors
        dots = self.dots
        for d in dots:
            fn(d, dots[d.ldot_idx], dots[d.rdot_idx], dots[d.opp_idx],
               avg_div, blend_div)
        if evolve_glyphs:
            for d in dots:
                d.evolve_glyph(step)

    def evolve(self, avg_div, blend_div, step=0, evolve_glyphs=True):
        self._step("e", avg_div, blend_div, step, evolve_glyphs)

    def devolve(self, avg_div, blend_div, step=0, evolve_glyphs=True):
        self._step("d", avg_div, blend_div, step, evolve_glyphs)

    def display(self):
        sys.stdout.write("".join(d.get_str() for d in self.dots) + "\n")
        sys.stdout.flush()


# ---------------------------------------------------------------------------
# Capture tee
# ---------------------------------------------------------------------------

@contextmanager
def capture_tee(path: str | None):
    if path is None:
        yield
        return
    real = sys.stdout
    buf = []
    class Tee:
        def write(self, s): real.write(s); buf.append(s)
        def flush(self): real.flush()
    sys.stdout = Tee()
    try:
        yield
    finally:
        sys.stdout = real
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text("".join(buf))
        print(f"\n[capture → {path}]", file=sys.stderr)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def do_art(cycles: int, mode: str, glyph_set: str, speed: float,
           evolve_glyphs: bool) -> None:
    line  = Line(glyph_set)
    total = cycles * 2

    for i in range(cycles):
        e_avg, e_bld, _, _ = get_distort_params(mode, i, total)
        line.evolve(e_avg, e_bld, step=i, evolve_glyphs=evolve_glyphs)
        line.display()
        if speed > 0:
            time.sleep(speed)

    for i in range(cycles):
        _, _, d_avg, d_bld = get_distort_params(mode, cycles + i, total)
        line.devolve(d_avg, d_bld, step=cycles + i, evolve_glyphs=evolve_glyphs)
        line.display()
        if speed > 0:
            time.sleep(speed)


def parse_args():
    p = argparse.ArgumentParser(
        description="Terminal cellular automaton — color phase oscillation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
distort modes:
  original     Dusty's magic numbers (gain +3.4%/cycle)
  sine         π-based — 142,694× in 40 cycles, maximum chaos
  golden       φ-based — organic spiraling (gain +5.8%/cycle)
  quantum      oscillating divisors — shimmer/interference
  monstertruck BOTH phases amplify — 1,782× in 40 cycles
  breathing    pulsing growth/decay oscillation
  critical     knife-edge — only 1.30× in 40 cycles, slow crystallization

glyph styles:
  block   ▤▥▦▧▨▩  (default)
  braille ⠀⠁⠃⠅…  (146 characters, fine texture)
  rune    ᚠᚢᚦᚨ…  (Elder Futhark)
  kanji   道気空風…  (elemental)
  math    ∀∃∅∆∇…  (mathematical)
  chaos   ◈◉◊○…  (geometric)
  ascii   @#$%…   (classic)
        """,
    )
    p.add_argument("cycles", nargs="?", type=int, default=40,
                   help="Frames per phase (default: 40)")
    p.add_argument("--mode", "-m", default="original",
                   choices=list(get_distort_params.__code__.co_consts
                                if False else
                                ["original", "sine", "golden", "quantum",
                                 "monstertruck", "breathing", "critical"]),
                   help="Distort mode (default: original)")
    p.add_argument("--glyphs", "-g", default="block",
                   choices=list(GLYPH_SETS.keys()),
                   help="Glyph style (default: block)")
    p.add_argument("--speed", "-s", type=float, default=0.02,
                   help="Delay between frames in seconds (default: 0.02)")
    p.add_argument("--static-glyphs", action="store_true",
                   help="Keep glyphs fixed (don't evolve with color)")
    p.add_argument("--capture", metavar="PATH",
                   help="Tee output to .ans file (e.g. museum/run.ans)")
    p.add_argument("--info", action="store_true",
                   help="Show mode parameters and predicted behavior, then exit")
    return p.parse_args()


def main():
    args = parse_args()

    if args.info:
        describe_mode(args.mode, args.cycles)
        return

    try:
        with capture_tee(args.capture):
            do_art(
                cycles      = args.cycles,
                mode        = args.mode,
                glyph_set   = args.glyphs,
                speed       = args.speed,
                evolve_glyphs = not args.static_glyphs,
            )
    except KeyboardInterrupt:
        sys.stdout.write("\x1b[0m\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
