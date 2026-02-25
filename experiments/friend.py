#!/usr/bin/env python3
"""
friend.py — 1D mirrored diffusion automata.

A single row of cells evolves through paired evolve/devolve cycles.
Each cell blends with its left neighbor, right neighbor, and its
"opposite" (mirror index across the center) — but the divisors are
irrational, preventing equilibrium.

THE MAGIC NUMBERS
-----------------
Evolve uses divisors slightly BELOW the neutral values (4 and 2),
so the system amplifies ~3.9% per step. Devolve uses divisors
slightly ABOVE neutral, damping ~0.5% per step. The asymmetry means
evolve and devolve are not inverses — they breathe.

  evolve avg divisor    3.759 ≈ π + 1/φ  (transcendental, truncated)
  evolve update divisor 1.986 ≈ 2 − 7/500 (slight amplification)
  devolve avg divisor   4.008 = 4 + 1/5³  (slight damping)
  devolve update divisor 2.008 = 2 + 1/5³  (matched damping)

The π + 1/φ origin of 3.759 means the averaging step draws on two
incommensurate irrationals simultaneously. No color value ever
revisits exactly the same arithmetic path. The 255-modulo display
wrapping turns long amplification runs into traveling color waves.

Run from repo root:
  python3 experiments/friend.py
  python3 experiments/friend.py 100      # 100 evolve + 100 devolve steps
"""

from random import randint
import os
import sys


class Dot:

    def __init__(self, idx):
        self.idx = idx
        self.fr = randint(0, 255)
        self.fg = randint(0, 255)
        self.fb = randint(0, 255)
        self.br = randint(0, 255)
        self.bg = randint(0, 255)
        self.bb = randint(0, 255)
        self.glyph = "▤"
        # Neighbor indices pre-computed by Line
        self.ldot_idx = None
        self.rdot_idx = None
        self.opp_idx = None

    def get_str(self):
        return (
            f"\x1b[38;2;{self.fr % 255};{self.fg % 255};{self.fb % 255}m"
            f"\x1b[48;2;{self.br % 255};{self.bg % 255};{self.bb % 255}m"
            f"{self.glyph}\x1b[0m"
        )

    def evolve_with_neighbors(self, ldot, rdot, opp):
        ofr, ofg, ofb = self.fr, self.fg, self.fb
        obr, obg, obb = self.br, self.bg, self.bb

        # Average with left, right, and opposite's background
        # Divisor 3.759 ≈ π + 1/φ — below 4, so amplifying
        avgfr = (ofr + ldot.fr + rdot.fr + opp.br) / 3.759
        avgfg = (ofg + ldot.fg + rdot.fg + opp.bg) / 3.759
        avgfb = (ofb + ldot.fb + rdot.fb + opp.bb) / 3.759
        avgbr = (obr + ldot.br + rdot.br + opp.fr) / 3.759
        avgbg = (obg + ldot.bg + rdot.bg + opp.fg) / 3.759
        avgbb = (obb + ldot.bb + rdot.bb + opp.fb) / 3.759

        # Blend old with average — divisor 1.986 below 2, amplifying
        self.fr = int((ofr + avgfr) / 1.986)
        self.fg = int((ofg + avgfg) / 1.986)
        self.fb = int((ofb + avgfb) / 1.986)
        self.br = int((obr + avgbr) / 1.986)
        self.bg = int((obg + avgbg) / 1.986)
        self.bb = int((obb + avgbb) / 1.986)

    def devolve_with_neighbors(self, ldot, rdot, opp):
        ofr, ofg, ofb = self.fr, self.fg, self.fb
        obr, obg, obb = self.br, self.bg, self.bb

        # Divisor 4.008 = 4 + 1/5³ — above 4, so damping
        avgfr = (ofr + ldot.fr + rdot.fr + opp.br) / 4.008
        avgfg = (ofg + ldot.fg + rdot.fg + opp.bg) / 4.008
        avgfb = (ofb + ldot.fb + rdot.fb + opp.bb) / 4.008
        avgbr = (obr + ldot.br + rdot.br + opp.fr) / 4.008
        avgbg = (obg + ldot.bg + rdot.bg + opp.fg) / 4.008
        avgbb = (obb + ldot.bb + rdot.bb + opp.fb) / 4.008

        # Divisor 2.008 = 2 + 1/5³ — above 2, so damping
        self.fr = int((ofr + avgfr) / 2.008)
        self.fg = int((ofg + avgfg) / 2.008)
        self.fb = int((ofb + avgfb) / 2.008)
        self.br = int((obr + avgbr) / 2.008)
        self.bg = int((obg + avgbg) / 2.008)
        self.bb = int((obb + avgbb) / 2.008)


class Line:

    def __init__(self):
        self.line = []
        width = os.get_terminal_size().columns

        for i in range(width):
            self.line.append(Dot(i))

        # Pre-compute neighbor indices
        for i, dot in enumerate(self.line):
            dot.ldot_idx = (i - 1) % width
            dot.rdot_idx = (i + 1) % width
            dot.opp_idx = abs(width - 1 - i)

    def evolve(self):
        for dot in self.line:
            dot.evolve_with_neighbors(
                self.line[dot.ldot_idx],
                self.line[dot.rdot_idx],
                self.line[dot.opp_idx],
            )

    def devolve(self):
        for dot in self.line:
            dot.devolve_with_neighbors(
                self.line[dot.ldot_idx],
                self.line[dot.rdot_idx],
                self.line[dot.opp_idx],
            )

    def display(self):
        sys.stdout.write("".join(d.get_str() for d in self.line))
        sys.stdout.flush()


def do_art(in_len):
    line = Line()
    for _ in range(in_len):
        line.evolve()
        line.display()
    for _ in range(in_len):
        line.devolve()
        line.display()


if __name__ == "__main__":
    steps = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    do_art(steps)
