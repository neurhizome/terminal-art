#!/usr/bin/env python3
"""
friend_enhanced.py — 1D mirrored diffusion automata, enhanced.

Extends friend.py with tunable magic constants, time-varying distort
modes, and palette-driven glyph selection.

DISTORT MODES
-------------
  none    — static divisors (original behavior)
  sine    — divisors oscillate sinusoidally around their base values
  golden  — quasi-periodic modulation using φ (incommensurate with sine)
  noise   — Gaussian perturbation of divisors each tick
  quantum — divisors jump between discrete "energy states" periodically

GLYPH PALETTES
--------------
  fill    — ▤ ▦ ▧ ▨ ▩  (original + variants, intensity-mapped)
  shade   — ░ ▒ ▓ █     (density maps directly to brightness)
  box     — ─ │ ┌ ┐ └ ┘  (box-drawing; structure emerges from color diff)
  braille — ⠁ ⠃ ⠇ ⠿ …   (64-level braille, highest glyph density)
  arrows  — ← ↑ → ↓ ↔   (direction from neighbor asymmetry)
  musical — ♩ ♪ ♫ ♬ ♭ ♮ ♯  (plays best with golden distort mode)
  organic — · ∘ ○ ● ◎ ⊙  (radial; feels like spore propagation)

Run from repo root:
  python3 experiments/friend_enhanced.py
  python3 experiments/friend_enhanced.py --distort-mode golden --palette musical
  python3 experiments/friend_enhanced.py --evolve-avg 3.5 --devolve-avg 4.2 --steps 400
  python3 experiments/friend_enhanced.py --distort-mode sine --distort-amp 0.15 --save-field /tmp/field.json
"""

import argparse
import json
import math
import os
import random
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# Glyph palettes — inline, no JSON database required
# Selected for visual rhythm and terminal compatibility
# ---------------------------------------------------------------------------

PALETTES = {
    "fill":    ["▤", "▦", "▧", "▨", "▩", "▪", "▫"],
    "shade":   [" ", "░", "▒", "▓", "█"],
    "box":     ["─", "│", "┼", "┌", "┐", "└", "┘", "├", "┤", "┬", "┴",
                "═", "║", "╔", "╗", "╚", "╝", "╬"],
    "braille": [
        "⠀", "⠁", "⠃", "⠇", "⠏", "⠟", "⠿",
        "⡀", "⡄", "⡆", "⡇", "⣇", "⣧", "⣷", "⣿",
        "⠤", "⠶", "⠾", "⣤", "⣶", "⣾", "⣿",
    ],
    "arrows":  ["←", "↖", "↑", "↗", "→", "↘", "↓", "↙", "↔", "↕"],
    "musical": ["♩", "♪", "♫", "♬", "♭", "♮", "♯"],
    "organic": ["·", "∘", "○", "◌", "◍", "◎", "●", "⊙", "⊚", "⊛"],
}

PHI = (1.0 + math.sqrt(5)) / 2.0   # golden ratio


# ---------------------------------------------------------------------------
# Distort parameter container
# ---------------------------------------------------------------------------

@dataclass
class DistortParams:
    """Current values of the four magic divisors."""
    evolve_avg: float
    evolve_update: float
    devolve_avg: float
    devolve_update: float


# Magic number defaults — see module docstring of friend.py for derivation
DEFAULT_PARAMS = DistortParams(
    evolve_avg=3.759,      # ≈ π + 1/φ  (amplifying)
    evolve_update=1.986,   # ≈ 2 − 7/500 (amplifying)
    devolve_avg=4.008,     # = 4 + 1/5³  (damping)
    devolve_update=2.008,  # = 2 + 1/5³  (damping)
)


# ---------------------------------------------------------------------------
# Distort mode implementations
# ---------------------------------------------------------------------------

def _distort_none(tick: int, base: DistortParams, amp: float) -> DistortParams:
    return base


def _distort_sine(tick: int, base: DistortParams, amp: float) -> DistortParams:
    """Sinusoidal modulation at period 60 ticks."""
    t = 2 * math.pi * tick / 60
    return DistortParams(
        evolve_avg=base.evolve_avg + amp * math.sin(t),
        evolve_update=base.evolve_update + amp * math.sin(t + math.pi / 4),
        devolve_avg=base.devolve_avg + amp * math.sin(t + math.pi / 2),
        devolve_update=base.devolve_update + amp * math.sin(t + 3 * math.pi / 4),
    )


def _distort_golden(tick: int, base: DistortParams, amp: float) -> DistortParams:
    """Quasi-periodic modulation: four channels use φ-multiples of frequency.

    Because φ is irrational, the four oscillators never repeat in phase —
    creating the same non-periodic breathing that φ produces in Fibonacci
    spirals and quasicrystals.
    """
    def g(freq_mul: float, phase: float) -> float:
        return amp * math.sin(2 * math.pi * PHI * freq_mul * tick / 60 + phase)

    return DistortParams(
        evolve_avg=base.evolve_avg + g(1.0, 0.0),
        evolve_update=base.evolve_update + g(PHI, math.pi / 3),
        devolve_avg=base.devolve_avg + g(PHI ** 2, 2 * math.pi / 3),
        devolve_update=base.devolve_update + g(PHI ** 3, math.pi),
    )


def _distort_noise(tick: int, base: DistortParams, amp: float) -> DistortParams:
    """Gaussian perturbation — each tick is independent."""
    return DistortParams(
        evolve_avg=base.evolve_avg + random.gauss(0, amp),
        evolve_update=base.evolve_update + random.gauss(0, amp / 2),
        devolve_avg=base.devolve_avg + random.gauss(0, amp),
        devolve_update=base.devolve_update + random.gauss(0, amp / 2),
    )


def _distort_quantum(tick: int, base: DistortParams, amp: float) -> DistortParams:
    """Discrete energy states — jumps every 30 ticks using φ-spaced levels.

    Five states per parameter, spaced at 0, ±amp/2, ±amp.
    The state index cycles through using floor(tick/30) mod 5.
    """
    states = [-amp, -amp / 2, 0.0, amp / 2, amp]
    era = (tick // 30) % len(states)
    # Each parameter gets a different offset into the state sequence
    return DistortParams(
        evolve_avg=base.evolve_avg + states[era % len(states)],
        evolve_update=base.evolve_update + states[(era + 1) % len(states)],
        devolve_avg=base.devolve_avg + states[(era + 2) % len(states)],
        devolve_update=base.devolve_update + states[(era + 3) % len(states)],
    )


DISTORT_FNS = {
    "none": _distort_none,
    "sine": _distort_sine,
    "golden": _distort_golden,
    "noise": _distort_noise,
    "quantum": _distort_quantum,
}


# ---------------------------------------------------------------------------
# Dot: single cell
# ---------------------------------------------------------------------------

class Dot:

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
        self.opp_idx: int = 0

    def select_glyph(self, palette_name: str, ldot: "Dot", opp: "Dot") -> str:
        """Choose a glyph from the palette based on local field state.

        Intensity (foreground brightness) indexes into the palette.
        For palettes that carry direction meaning (arrows), the
        asymmetry between left and opposite neighbors biases selection.
        """
        palette = PALETTES[palette_name]

        # Normalized foreground brightness [0, 1)
        intensity = (self.fr + self.fg + self.fb) / (255.0 * 3.0)

        if palette_name == "arrows":
            # Direction from color asymmetry: left vs opposite-bg
            diff = ((self.fr - opp.br) + (self.fg - opp.bg) + (self.fb - opp.bb)) / (255.0 * 3.0)
            # Map diff in [-1, 1] to index
            idx = int((diff + 1.0) / 2.0 * len(palette)) % len(palette)
            return palette[idx]

        if palette_name == "braille":
            # Braille: density follows intensity directly
            idx = int(intensity * len(palette)) % len(palette)
            return palette[idx]

        # Default: intensity-indexed with slight neighbor-diff jitter
        neighbor_brightness = (ldot.fr + ldot.fg + ldot.fb) / (255.0 * 3.0)
        jitter = abs(intensity - neighbor_brightness) * 0.3
        idx = int((intensity + jitter) * len(palette)) % len(palette)
        return palette[idx]

    def get_str(self) -> str:
        return (
            f"\x1b[38;2;{self.fr % 255};{self.fg % 255};{self.fb % 255}m"
            f"\x1b[48;2;{self.br % 255};{self.bg % 255};{self.bb % 255}m"
            f"{self.glyph}\x1b[0m"
        )

    def to_dict(self) -> dict:
        return {
            "fr": self.fr, "fg": self.fg, "fb": self.fb,
            "br": self.br, "bg": self.bg, "bb": self.bb,
        }

    def evolve_with_neighbors(self, ldot: "Dot", rdot: "Dot", opp: "Dot",
                               p: DistortParams) -> None:
        ofr, ofg, ofb = self.fr, self.fg, self.fb
        obr, obg, obb = self.br, self.bg, self.bb

        ea = max(p.evolve_avg, 0.001)   # guard against divide-by-zero
        eu = max(p.evolve_update, 0.001)

        avgfr = (ofr + ldot.fr + rdot.fr + opp.br) / ea
        avgfg = (ofg + ldot.fg + rdot.fg + opp.bg) / ea
        avgfb = (ofb + ldot.fb + rdot.fb + opp.bb) / ea
        avgbr = (obr + ldot.br + rdot.br + opp.fr) / ea
        avgbg = (obg + ldot.bg + rdot.bg + opp.fg) / ea
        avgbb = (obb + ldot.bb + rdot.bb + opp.fb) / ea

        self.fr = int((ofr + avgfr) / eu)
        self.fg = int((ofg + avgfg) / eu)
        self.fb = int((ofb + avgfb) / eu)
        self.br = int((obr + avgbr) / eu)
        self.bg = int((obg + avgbg) / eu)
        self.bb = int((obb + avgbb) / eu)

    def devolve_with_neighbors(self, ldot: "Dot", rdot: "Dot", opp: "Dot",
                                p: DistortParams) -> None:
        ofr, ofg, ofb = self.fr, self.fg, self.fb
        obr, obg, obb = self.br, self.bg, self.bb

        da = max(p.devolve_avg, 0.001)
        du = max(p.devolve_update, 0.001)

        avgfr = (ofr + ldot.fr + rdot.fr + opp.br) / da
        avgfg = (ofg + ldot.fg + rdot.fg + opp.bg) / da
        avgfb = (ofb + ldot.fb + rdot.fb + opp.bb) / da
        avgbr = (obr + ldot.br + rdot.br + opp.fr) / da
        avgbg = (obg + ldot.bg + rdot.bg + opp.fg) / da
        avgbb = (obb + ldot.bb + rdot.bb + opp.fb) / da

        self.fr = int((ofr + avgfr) / du)
        self.fg = int((ofg + avgfg) / du)
        self.fb = int((ofb + avgfb) / du)
        self.br = int((obr + avgbr) / du)
        self.bg = int((obg + avgbg) / du)
        self.bb = int((obb + avgbb) / du)


# ---------------------------------------------------------------------------
# Line: the 1D automaton
# ---------------------------------------------------------------------------

class Line:

    def __init__(self, palette: str = "fill"):
        self.palette = palette
        self.line: list[Dot] = []
        width = os.get_terminal_size().columns

        for i in range(width):
            self.line.append(Dot(i))

        for i, dot in enumerate(self.line):
            dot.ldot_idx = (i - 1) % width
            dot.rdot_idx = (i + 1) % width
            dot.opp_idx = abs(width - 1 - i)

    def _step(self, method: str, params: DistortParams) -> None:
        fn = "evolve_with_neighbors" if method == "evolve" else "devolve_with_neighbors"
        for dot in self.line:
            getattr(dot, fn)(
                self.line[dot.ldot_idx],
                self.line[dot.rdot_idx],
                self.line[dot.opp_idx],
                params,
            )
        # Update glyphs after each tick
        if self.palette != "fill" or True:
            for dot in self.line:
                dot.glyph = dot.select_glyph(
                    self.palette,
                    self.line[dot.ldot_idx],
                    self.line[dot.opp_idx],
                )

    def evolve(self, params: DistortParams) -> None:
        self._step("evolve", params)

    def devolve(self, params: DistortParams) -> None:
        self._step("devolve", params)

    def display(self) -> None:
        sys.stdout.write("".join(d.get_str() for d in self.line))
        sys.stdout.flush()

    def save_field(self, filepath: str, metadata: dict) -> None:
        """Dump the current color field state to JSON."""
        data = {
            "metadata": metadata,
            "timestamp": datetime.utcnow().isoformat(),
            "cells": [d.to_dict() for d in self.line],
        }
        Path(filepath).write_text(json.dumps(data, indent=2))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="friend_enhanced — 1D mirrored diffusion automata",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--evolve-avg", type=float, default=3.759, metavar="D",
                   help="Evolve averaging divisor (default: 3.759 ≈ π+1/φ)")
    p.add_argument("--evolve-update", type=float, default=1.986, metavar="D",
                   help="Evolve blend divisor (default: 1.986)")
    p.add_argument("--devolve-avg", type=float, default=4.008, metavar="D",
                   help="Devolve averaging divisor (default: 4.008 = 4+1/5³)")
    p.add_argument("--devolve-update", type=float, default=2.008, metavar="D",
                   help="Devolve blend divisor (default: 2.008 = 2+1/5³)")
    p.add_argument("--distort-mode", choices=list(DISTORT_FNS), default="none",
                   help="Time-varying modulation of divisors (default: none)")
    p.add_argument("--distort-amp", type=float, default=0.1, metavar="A",
                   help="Modulation amplitude for distort modes (default: 0.1)")
    p.add_argument("--palette", choices=list(PALETTES), default="fill",
                   help="Glyph palette (default: fill)")
    p.add_argument("--steps", type=int, default=200, metavar="N",
                   help="Number of evolve + devolve steps each (default: 200)")
    p.add_argument("--save-field", metavar="PATH",
                   help="Save final color field state to this JSON path")
    return p.parse_args()


def do_art(args: argparse.Namespace) -> None:
    base = DistortParams(
        evolve_avg=args.evolve_avg,
        evolve_update=args.evolve_update,
        devolve_avg=args.devolve_avg,
        devolve_update=args.devolve_update,
    )
    distort_fn = DISTORT_FNS[args.distort_mode]
    line = Line(palette=args.palette)

    tick = 0
    for _ in range(args.steps):
        params = distort_fn(tick, base, args.distort_amp)
        line.evolve(params)
        line.display()
        tick += 1

    for _ in range(args.steps):
        params = distort_fn(tick, base, args.distort_amp)
        line.devolve(params)
        line.display()
        tick += 1

    if args.save_field:
        metadata = {
            "steps": args.steps,
            "distort_mode": args.distort_mode,
            "distort_amp": args.distort_amp,
            "palette": args.palette,
            "evolve_avg": args.evolve_avg,
            "evolve_update": args.evolve_update,
            "devolve_avg": args.devolve_avg,
            "devolve_update": args.devolve_update,
            "total_ticks": tick,
        }
        line.save_field(args.save_field, metadata)
        print(f"\nField saved to {args.save_field}", file=sys.stderr)


if __name__ == "__main__":
    do_art(parse_args())
