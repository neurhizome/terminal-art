#!/usr/bin/env python3

from random import randint, choice
import os
import sys

class Dot:

    def __init__(self, idx):
        self.idx = idx
        self.fr = randint(0,255)
        self.fg = randint(0,255)
        self.fb = randint(0,255)
        self.br = randint(0,255)
        self.bg = randint(0,255)
        self.bb = randint(0,255)
        self.glyph = "▩"
        # Neighbor indices pre-computed by Line
        self.ldot_idx = None
        self.rdot_idx = None
        self.opp_idx = None

    def get_str(self):
        return f"\x1b[38;2;{self.fr % 255};{self.fg % 255};{self.fb % 255}m\x1b[48;2;{self.br % 255};{self.bg % 255};{self.bb % 255}m{self.glyph}\x1b[0m"

    def evolve_with_neighbors(self, ldot, rdot, opp):

        # Store old values
        ofr, ofg, ofb = self.fr, self.fg, self.fb
        obr, obg, obb = self.br, self.bg, self.bb

        # Compute averages with the magical 3.976 divisor
        avgfr = (ofr + ldot.fr + rdot.fr + opp.br) / 3.984
        avgfg = (ofg + ldot.fg + rdot.fg + opp.bg) / 3.984
        avgfb = (ofb + ldot.fb + rdot.fb + opp.bb) / 3.984
        avgbr = (obr + ldot.br + rdot.br + opp.fr) / 3.984
        avgbg = (obg + ldot.bg + rdot.bg + opp.fg) / 3.984
        avgbb = (obb + ldot.bb + rdot.bb + opp.fb) / 3.984

        # Update with the magical 1.976 divisor
        self.fr = int((ofr + avgfr) / 1.993)
        self.fg = int((ofg + avgfg) / 1.993)
        self.fb = int((ofb + avgfb) / 1.993)
        self.br = int((obr + avgbr) / 1.993)
        self.bg = int((obg + avgbg) / 1.993)
        self.bb = int((obb + avgbb) / 1.993)


class Line:

    def __init__(self):
        self.line = []
        width = os.get_terminal_size().columns

        # Create all dots
        for i in range(width):
            self.line.append(Dot(i))

        # Pre-compute neighbor indices for each dot
        for i, dot in enumerate(self.line):
            dot.ldot_idx = (i - 1) % width
            dot.rdot_idx = (i + 1) % width
            dot.opp_idx = abs(width - 1 - (i % 7))

    def evolve(self):
        """Evolve all dots in place"""
        for dot in self.line:
            dot.evolve_with_neighbors(
                self.line[dot.ldot_idx],
                self.line[dot.rdot_idx],
                self.line[dot.opp_idx]
            )

    def display(self):
        # Compose string then write once
        sys.stdout.write(''.join(d.get_str() for d in self.line))
        sys.stdout.flush()

def do_art(in_len):
    line = Line()
    for i in range(in_len):
        line.evolve()
        line.display()
