#!/usr/bin/env python3
"""
friend_oscillator.py — Tension geometry and moiré emergence in 1D diffusion.

THE TENSION GEOMETRY
--------------------
The "correct" divisors produce a perfectly neutral system (no drift):
  correct_avg = 4.0   (average of exactly 4 values)
  correct_upd = 2.0   (blend of exactly old + new)

The devolve pair sits above correct by δ = 1/5³ = 0.008:
  devolve_avg = 4.008 = correct_avg + δ   → damping
  devolve_upd = 2.008 = correct_upd + δ   → damping

THE OPTIMAL EVOLVE DIVISOR
---------------------------
If devolve_surplus = δ = 0.008, then the "balanced tension" point —
where evolve amplifies at exactly twice the rate devolve damps —
is at deficit = 2δ:

  optimal_evolve_avg = 4.0 - 2δ = 4.0 - 0.016 = 3.984

At 3.759 (the original magic number), deficit = 0.241 → ratio = 15×
At 3.984 (optimal), deficit = 0.016 → ratio = 1.00×
At 3.991 (near-correct), deficit = 0.009 → ratio = 0.56×

Gain per step (homogeneous field):
  3.759 → evolve +3.93%,  devolve −0.50%  → net +3.41% per cycle
  3.984 → evolve +0.91%,  devolve −0.50%  → net +0.40% per cycle
  4.000 → evolve +0.71%,  devolve −0.50%  → net +0.20% per cycle (still drifts!)

THE OSCILLATOR
--------------
Two coupled oscillators modulate evolve_avg and devolve_avg using
Fibonacci periods 89 and 55. Their beat frequency = |1/89 − 1/55|
has period exactly 144 — another Fibonacci number.

At each 144-tick moiré cycle, both oscillators briefly phase-align,
creating a "double tension" pulse where maximum emergence occurs.

GLYPH SYSTEM
------------
Glyphs are selected per-cell by tension ratio and oscillator phase:

  ratio < 0.3   → sparse organic     (· ∘ ○ ◌)  under-tensioned
  ratio 0.3-0.7 → rising geometric   (◍ ◎ ▒ ▤)
  ratio 0.7-1.3 → RESONANCE ZONE     (phase-cycling musical/braille)
  ratio 1.3-3.0 → dense fill         (▦ ▧ ▨ ▩ ▓)
  ratio > 3.0   → maximum density    (░ ▒ ▓ █)  explosive range

TENSION BAND
------------
Every BAND_INTERVAL lines, a full-width color band is rendered showing
the current divisor positions on a number line. This becomes part of
the art — horizontal markers of the oscillator's rhythm.

Run from repo root:
  python3 experiments/friend_oscillator.py
  python3 experiments/friend_oscillator.py --sweep
  python3 experiments/friend_oscillator.py --capture museum/osc-$(date +%s).ans
  python3 experiments/friend_oscillator.py --base-evolve 3.759 --amplitude 0.05
  python3 experiments/friend_oscillator.py --base-evolve 3.991 --steps 400
"""

import argparse
import math
import os
import random
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Tension geometry constants
# ---------------------------------------------------------------------------

PHI = (1.0 + math.sqrt(5)) / 2.0      # golden ratio
FIB = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233]

CORRECT_AVG = 4.0
CORRECT_UPD = 2.0

DEVOLVE_AVG    = 4.008                 # = CORRECT_AVG + 1/5³
DEVOLVE_UPD    = 2.008                 # = CORRECT_UPD + 1/5³
DEVOLVE_SURPLUS = DEVOLVE_AVG - CORRECT_AVG   # δ = 0.008

OPTIMAL_EVOLVE_AVG = CORRECT_AVG - 2 * DEVOLVE_SURPLUS   # 3.984
ORIGINAL_MAGIC_AVG = 3.759            # original friend.py value (ratio ≈ 15×)
NEAR_CORRECT_AVG   = 3.991            # near-correct, ratio ≈ 0.56×

# Fibonacci oscillator periods — beat period = 144 ticks exactly
PERIOD_E = 89
PERIOD_D = 55

# ---------------------------------------------------------------------------
# Glyph palettes keyed by tension regime
# ---------------------------------------------------------------------------

# Sparse: used when tension ratio < 0.3 (under-tensioned, boring)
GLYPHS_SPARSE   = list("·∘○◌    ·∘○")

# Rising: ratio 0.3–0.7
GLYPHS_RISING   = list("◍◎▒▤◦⊙◌◍")

# Resonance zone: ratio 0.7–1.3, cycles through phase-based sets
GLYPHS_RESONANCE = [
    list("♩♪♫♬♭♮♯♩♪♫"),           # musical — feels like the wolf interval
    list("⠁⠃⠇⠏⠟⠿⣿⣷⣧⣇"),          # braille density sweep
    list("─│┼├┤┬┴╔╗╚╝╬═║"),        # box-drawing: structure crystallizes
    list("↖↑↗→↘↓↙←↔↕"),           # arrows: direction field visible
]

# Dense: ratio 1.3–3.0
GLYPHS_DENSE    = list("▦▧▨▩▓▦▧▨▩")

# Maximum: ratio > 3.0 (original 3.759 territory, explosive)
GLYPHS_MAX      = list("░▒▓█▀▄▌▐▃▆▁▂")

# Tension band markers
BAND_CHAR_EVOLVE  = "◆"
BAND_CHAR_DEVOLVE = "◇"
BAND_CHAR_CORRECT = "│"
BAND_CHAR_OPTIMAL = "‖"
BAND_CHAR_FILL    = "─"

BAND_INTERVAL = 15    # render a tension band every N art lines


# ---------------------------------------------------------------------------
# Tension state
# ---------------------------------------------------------------------------

@dataclass
class TensionState:
    evolve_avg:  float
    evolve_upd:  float
    devolve_avg: float
    devolve_upd: float
    tick:        int = 0

    @property
    def evolve_deficit(self) -> float:
        return CORRECT_AVG - self.evolve_avg        # positive = amplifying

    @property
    def devolve_surplus(self) -> float:
        return self.devolve_avg - CORRECT_AVG       # positive = damping

    @property
    def tension_ratio(self) -> float:
        """evolve_deficit / (2 × devolve_surplus).  1.0 = optimal balance."""
        denom = 2.0 * max(abs(self.devolve_surplus), 1e-9)
        return self.evolve_deficit / denom

    @property
    def evolve_gain(self) -> float:
        ea = max(self.evolve_avg, 1e-6)
        eu = max(self.evolve_upd, 1e-6)
        return (1.0 + 4.0 / ea) / eu

    @property
    def devolve_gain(self) -> float:
        da = max(self.devolve_avg, 1e-6)
        du = max(self.devolve_upd, 1e-6)
        return (1.0 + 4.0 / da) / du

    @property
    def net_gain_per_cycle(self) -> float:
        return self.evolve_gain * self.devolve_gain

    @property
    def phase_sector(self) -> int:
        """Which resonance glyph set to use (0–3), based on oscillator phase."""
        phase = (2 * math.pi * self.tick / PERIOD_E) % (2 * math.pi)
        return int(phase / (math.pi / 2)) % len(GLYPHS_RESONANCE)

    def glyph_list(self) -> list:
        r = self.tension_ratio
        if r < 0.3:
            return GLYPHS_SPARSE
        elif r < 0.7:
            return GLYPHS_RISING
        elif r < 1.3:
            return GLYPHS_RESONANCE[self.phase_sector]
        elif r < 3.0:
            return GLYPHS_DENSE
        else:
            return GLYPHS_MAX


# ---------------------------------------------------------------------------
# Tension oscillator — two Fibonacci-period coupled oscillators
# ---------------------------------------------------------------------------

class TensionOscillator:
    """
    Modulates evolve_avg and devolve_avg around their base values using
    two sinusoidal oscillators with Fibonacci periods (89, 55).

    Beat period = LCM-related: |1/89 - 1/55| → period = 144 ticks.
    At each 144-tick beat, both oscillators align → double tension pulse.

    A second harmonic (at φ × frequency) adds quasi-periodic texture.
    """

    def __init__(
        self,
        base_evolve_avg:  float = OPTIMAL_EVOLVE_AVG,
        base_evolve_upd:  float = 1.986,
        base_devolve_avg: float = DEVOLVE_AVG,
        base_devolve_upd: float = DEVOLVE_UPD,
        amplitude:        float = 0.016,
        e_period:         int   = PERIOD_E,
        d_period:         int   = PERIOD_D,
    ):
        self.base_e_avg = base_evolve_avg
        self.base_e_upd = base_evolve_upd
        self.base_d_avg = base_devolve_avg
        self.base_d_upd = base_devolve_upd
        self.amplitude  = amplitude
        self.e_period   = e_period
        self.d_period   = d_period

    def get_state(self, tick: int) -> TensionState:
        t_e = 2.0 * math.pi * tick / self.e_period
        t_d = 2.0 * math.pi * tick / self.d_period

        # Primary oscillation + golden-ratio second harmonic
        e_mod = self.amplitude * (
            math.sin(t_e) + 0.35 * math.sin(t_e * PHI)
        )
        # Devolve: half amplitude, phase-shifted by π/3
        d_mod = self.amplitude * 0.5 * (
            math.sin(t_d + math.pi / 3) + 0.2 * math.sin(t_d * PHI)
        )

        return TensionState(
            evolve_avg  = self.base_e_avg  + e_mod,
            evolve_upd  = self.base_e_upd,
            devolve_avg = self.base_d_avg  + d_mod,
            devolve_upd = self.base_d_upd,
            tick        = tick,
        )

    def phase_alignment(self, tick: int) -> float:
        """
        How closely aligned are the two oscillators right now?
        Returns 0.0 (anti-phase) to 1.0 (perfectly in-phase).
        """
        t_e = (2.0 * math.pi * tick / self.e_period) % (2.0 * math.pi)
        t_d = (2.0 * math.pi * tick / self.d_period) % (2.0 * math.pi)
        return (1.0 + math.cos(t_e - t_d)) / 2.0


# ---------------------------------------------------------------------------
# Dot
# ---------------------------------------------------------------------------

class Dot:

    __slots__ = ("idx", "fr", "fg", "fb", "br", "bg", "bb",
                 "glyph", "ldot_idx", "rdot_idx", "opp_idx")

    def __init__(self, idx: int):
        self.idx = idx
        self.fr = random.randint(0, 255)
        self.fg = random.randint(0, 255)
        self.fb = random.randint(0, 255)
        self.br = random.randint(0, 255)
        self.bg = random.randint(0, 255)
        self.bb = random.randint(0, 255)
        self.glyph = "▤"
        self.ldot_idx: int = 0
        self.rdot_idx: int = 0
        self.opp_idx:  int = 0

    def intensity(self) -> float:
        return (self.fr + self.fg + self.fb) / (255.0 * 3.0)

    def bg_intensity(self) -> float:
        return (self.br + self.bg + self.bb) / (255.0 * 3.0)

    def select_glyph(self, state: TensionState, opp: "Dot", ldot: "Dot") -> str:
        glyphs = state.glyph_list()

        fg_bright = self.intensity()
        opp_bg_bright = (opp.br + opp.bg + opp.bb) / (255.0 * 3.0)
        neighbor_bright = ldot.intensity()

        # Contrast with opposite neighbor (across the center mirror)
        contrast = abs(fg_bright - opp_bg_bright)

        # Slight bias from left neighbor similarity
        similarity = 1.0 - abs(fg_bright - neighbor_bright)

        combined = (fg_bright * 0.5 + contrast * 0.35 + similarity * 0.15)
        idx = int(combined * len(glyphs)) % len(glyphs)
        return glyphs[idx]

    def get_str(self) -> str:
        return (
            f"\x1b[38;2;{self.fr % 255};{self.fg % 255};{self.fb % 255}m"
            f"\x1b[48;2;{self.br % 255};{self.bg % 255};{self.bb % 255}m"
            f"{self.glyph}\x1b[0m"
        )

    def _avg_step(self, ldot: "Dot", rdot: "Dot", opp: "Dot", d: float):
        return (
            (self.fr + ldot.fr + rdot.fr + opp.br) / d,
            (self.fg + ldot.fg + rdot.fg + opp.bg) / d,
            (self.fb + ldot.fb + rdot.fb + opp.bb) / d,
            (self.br + ldot.br + rdot.br + opp.fr) / d,
            (self.bg + ldot.bg + rdot.bg + opp.fg) / d,
            (self.bb + ldot.bb + rdot.bb + opp.fb) / d,
        )

    def evolve(self, ldot: "Dot", rdot: "Dot", opp: "Dot", s: TensionState):
        ofr, ofg, ofb = self.fr, self.fg, self.fb
        obr, obg, obb = self.br, self.bg, self.bb
        ea = max(s.evolve_avg, 1e-6)
        eu = max(s.evolve_upd,  1e-6)
        afr, afg, afb, abr, abg, abb = self._avg_step(ldot, rdot, opp, ea)
        self.fr = int((ofr + afr) / eu)
        self.fg = int((ofg + afg) / eu)
        self.fb = int((ofb + afb) / eu)
        self.br = int((obr + abr) / eu)
        self.bg = int((obg + abg) / eu)
        self.bb = int((obb + abb) / eu)

    def devolve(self, ldot: "Dot", rdot: "Dot", opp: "Dot", s: TensionState):
        ofr, ofg, ofb = self.fr, self.fg, self.fb
        obr, obg, obb = self.br, self.bg, self.bb
        da = max(s.devolve_avg, 1e-6)
        du = max(s.devolve_upd,  1e-6)
        afr, afg, afb, abr, abg, abb = self._avg_step(ldot, rdot, opp, da)
        self.fr = int((ofr + afr) / du)
        self.fg = int((ofg + afg) / du)
        self.fb = int((ofb + afb) / du)
        self.br = int((obr + abr) / du)
        self.bg = int((obg + abg) / du)
        self.bb = int((obb + abb) / du)


# ---------------------------------------------------------------------------
# Line
# ---------------------------------------------------------------------------

class Line:

    def __init__(self, width: int | None = None):
        try:
            self.width = width or os.get_terminal_size().columns
        except OSError:
            self.width = width or int(os.environ.get("COLUMNS", 96))
        self.dots: list[Dot] = [Dot(i) for i in range(self.width)]
        for i, d in enumerate(self.dots):
            d.ldot_idx = (i - 1) % self.width
            d.rdot_idx = (i + 1) % self.width
            d.opp_idx  = abs(self.width - 1 - i)

    def _step(self, method: str, state: TensionState):
        fn = Dot.evolve if method == "evolve" else Dot.devolve
        dots = self.dots
        for d in dots:
            fn(d, dots[d.ldot_idx], dots[d.rdot_idx], dots[d.opp_idx], state)
        for d in dots:
            d.glyph = d.select_glyph(state, dots[d.opp_idx], dots[d.ldot_idx])

    def step_evolve(self, state: TensionState):
        self._step("evolve", state)

    def step_devolve(self, state: TensionState):
        self._step("devolve", state)

    def display(self):
        sys.stdout.write("".join(d.get_str() for d in self.dots) + "\n")
        sys.stdout.flush()

    def render_tension_band(self, state: TensionState, osc: TensionOscillator) -> str:
        """
        Full-width ANSI band encoding the current tension geometry.

        Maps the range [3.70, 4.30] onto the terminal width.
        Marks: optimal (3.984), correct (4.000), original (3.759),
               current evolve (◆), current devolve (◇).
        Hue shifts from red (high deficit/tension) through white
        (at correct=4.0) to blue (surplus/damping zone).
        """
        w = self.width
        lo, hi = 3.70, 4.30
        span = hi - lo

        def x_pos(val: float) -> int:
            return max(0, min(w - 1, int((val - lo) / span * w)))

        pos_optimal = x_pos(OPTIMAL_EVOLVE_AVG)   # 3.984
        pos_correct = x_pos(CORRECT_AVG)           # 4.000
        pos_original = x_pos(ORIGINAL_MAGIC_AVG)  # 3.759
        pos_evolve  = x_pos(state.evolve_avg)
        pos_devolve = x_pos(state.devolve_avg)

        alignment = osc.phase_alignment(state.tick)
        ratio = state.tension_ratio

        chars = [BAND_CHAR_FILL] * w
        chars[pos_optimal] = BAND_CHAR_OPTIMAL
        chars[pos_correct] = BAND_CHAR_CORRECT
        chars[pos_evolve]  = BAND_CHAR_EVOLVE
        chars[pos_devolve] = BAND_CHAR_DEVOLVE

        # ── Build per-cell fg/bg colors ──────────────────────────────────
        cell_fg = []
        cell_bg = []
        for i in range(w):
            x = (i / w - (pos_correct / w)) * 2.0
            if alignment > 0.95 and abs(i - pos_evolve) < 4:
                r, g, b = 255, 255, 255
            elif x < 0:
                t = min(1.0, -x)
                r = int(180 + 75 * t)
                g = int(80  - 60 * t)
                b = max(0, int(40 + 20 * t * max(ratio, 0) / 2))
            else:
                t = min(1.0, x * 3)
                r = int(30  + 20 * (1 - t))
                g = int(140 + 60 * (1 - t))
                b = int(200 + 55 * t)
            cell_fg.append((r, g, b))
            cell_bg.append((max(0, r - 60), max(0, g - 60), max(0, b - 60)))

        # ── Info text overlaid RIGHT-ALIGNED within the band ─────────────
        # Keeping total width = w avoids overflow onto a second terminal row.
        ratio_str = f"{ratio:.2f}\u00d7"          # × as unicode escape
        net_str   = f"net:{state.net_gain_per_cycle:.4f}"
        align_str = f"aln:{alignment:.2f}"
        tick_str  = f"T{state.tick:04d}"
        info = f" {ratio_str} {net_str} {align_str} {tick_str} "
        info = info[: w - 4]                       # cap; leave 4 landmark chars
        info_start = w - len(info)

        out = []
        for i, ch in enumerate(chars):
            r, g, b = cell_fg[i]
            br2, bg2, bb2 = cell_bg[i]
            if i >= info_start:
                # White text on band background — readable at any colour
                display = info[i - info_start]
                out.append(
                    f"\x1b[38;2;255;255;255m"
                    f"\x1b[48;2;{br2};{bg2};{bb2}m"
                    f"{display}\x1b[0m"
                )
            else:
                out.append(
                    f"\x1b[38;2;{r};{g};{b}m"
                    f"\x1b[48;2;{br2};{bg2};{bb2}m"
                    f"{ch}\x1b[0m"
                )

        return "".join(out) + "\n"


# ---------------------------------------------------------------------------
# Capture tee
# ---------------------------------------------------------------------------

@contextmanager
def capture_tee(path: str | None):
    """Tee stdout to a file while also writing to the real stdout."""
    if path is None:
        yield
        return
    real = sys.stdout
    buf = []
    class Tee:
        def write(self, s):
            real.write(s)
            buf.append(s)
        def flush(self):
            real.flush()
    sys.stdout = Tee()
    try:
        yield
    finally:
        sys.stdout = real
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text("".join(buf))
        print(f"\n[capture → {path}]", file=sys.stderr)


# ---------------------------------------------------------------------------
# Main art loop
# ---------------------------------------------------------------------------

def do_art(osc: TensionOscillator, steps: int = 270):
    line = Line()
    tick = 0
    line_count = 0

    def maybe_band(state: TensionState):
        nonlocal line_count
        if line_count % BAND_INTERVAL == 0:
            sys.stdout.write(line.render_tension_band(state, osc))
            sys.stdout.flush()
        line_count += 1

    # — Evolve phase —
    for _ in range(steps):
        state = osc.get_state(tick)
        line.step_evolve(state)
        maybe_band(state)
        line.display()
        tick += 1

    # — Devolve phase —
    for _ in range(steps):
        state = osc.get_state(tick)
        line.step_devolve(state)
        maybe_band(state)
        line.display()
        tick += 1


# ---------------------------------------------------------------------------
# Sweep mode — show the drastic effect of e_avg on emergence
# ---------------------------------------------------------------------------

def do_sweep(steps_per: int = 25):
    """
    Systematically walks e_avg from the original magic value (3.759)
    to the near-correct value (4.000), showing the visual character
    at each point. Inserts labeled bands between segments.
    """
    test_values = [
        (3.759, "ORIGINAL (ratio 15×) — explosive bloom"),
        (3.900, "RATIO 6.25× — fast moiré"),
        (3.950, "RATIO 3.12× — traveling waves"),
        (3.975, "RATIO 1.56× — crystallization zone"),
        (3.984, "OPTIMAL (ratio 1.00×) — maximum tension, slow moiré"),
        (3.991, "RATIO 0.56× — near-correct, sustained interference"),
        (3.995, "RATIO 0.31× — breath mode"),
        (4.000, "RATIO 0.00× — correct (net drift from e_upd=1.986 only)"),
    ]

    try:
        width = os.get_terminal_size().columns
    except OSError:
        width = int(os.environ.get("COLUMNS", 96))

    for e_avg, label in test_values:
        # Label band
        lbl_line = f"{'─' * 3} e_avg={e_avg:.3f}  {label} {'─' * 3}"
        lbl_line = lbl_line[:width]
        sys.stdout.write(f"\x1b[38;2;220;220;80m\x1b[48;2;30;30;30m{lbl_line:<{width}}\x1b[0m\n")
        sys.stdout.flush()

        osc = TensionOscillator(
            base_evolve_avg=e_avg,
            amplitude=0.0,   # static — no oscillation during sweep
        )
        line = Line()
        for t in range(steps_per):
            state = osc.get_state(t)
            line.step_evolve(state)
            line.display()
        for t in range(steps_per):
            state = osc.get_state(steps_per + t)
            line.step_devolve(state)
            line.display()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args():
    p = argparse.ArgumentParser(
        description="friend_oscillator — tension geometry and moiré emergence",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--base-evolve", type=float, default=OPTIMAL_EVOLVE_AVG,
                   metavar="D",
                   help=f"Base evolve_avg (default: {OPTIMAL_EVOLVE_AVG} = 4−2δ = optimal)")
    p.add_argument("--base-devolve", type=float, default=DEVOLVE_AVG,
                   metavar="D",
                   help=f"Base devolve_avg (default: {DEVOLVE_AVG} = 4+δ)")
    p.add_argument("--amplitude", type=float, default=0.016,
                   metavar="A",
                   help="Oscillator amplitude in divisor units (default: 0.016 = 2δ)")
    p.add_argument("--e-period", type=int, default=PERIOD_E,
                   metavar="N",
                   help=f"Evolve oscillator period in ticks (default: {PERIOD_E})")
    p.add_argument("--d-period", type=int, default=PERIOD_D,
                   metavar="N",
                   help=f"Devolve oscillator period in ticks (default: {PERIOD_D})")
    p.add_argument("--steps", type=int, default=270,
                   metavar="N",
                   help="Evolve steps (same count for devolve, default: 270)")
    p.add_argument("--sweep", action="store_true",
                   help="Sweep e_avg from 3.759→4.000, showing visual character at each")
    p.add_argument("--sweep-steps", type=int, default=25,
                   metavar="N",
                   help="Steps per value in sweep mode (default: 25)")
    p.add_argument("--capture", metavar="PATH",
                   help="Tee output to this .ans file (museum/filename.ans)")
    return p.parse_args()


def main():
    args = parse_args()
    with capture_tee(args.capture):
        if args.sweep:
            do_sweep(steps_per=args.sweep_steps)
        else:
            osc = TensionOscillator(
                base_evolve_avg  = args.base_evolve,
                base_devolve_avg = args.base_devolve,
                amplitude        = args.amplitude,
                e_period         = args.e_period,
                d_period         = args.d_period,
            )
            do_art(osc, steps=args.steps)


if __name__ == "__main__":
    main()
