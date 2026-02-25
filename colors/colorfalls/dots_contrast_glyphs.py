#!/usr/bin/env python3

from random import randint
import os
import sys

# Glyph pool ordered from low to high visual density
GLYPH_POOL = ['░', '▒', '▓', '█', '▀', '▄', '▌', '▐', '▖', '▗', '▘', '▝', '▞', '▟']

class Dot:

    def __init__(self, idx):
        self.idx = idx
        self.fr = randint(0,255)
        self.fg = randint(0,255)
        self.fb = randint(0,255)
        self.br = randint(0,255)
        self.bg = randint(0,255)
        self.bb = randint(0,255)
        self.glyph = GLYPH_POOL[randint(0, len(GLYPH_POOL)-1)]
        # Neighbor indices pre-computed by Line
        self.ldot_idx = None
        self.rdot_idx = None
        self.opp_idx = None

    def get_str(self):
        return f"\x1b[38;2;{self.fr % 255};{self.fg % 255};{self.fb % 255}m\x1b[48;2;{self.br % 255};{self.bg % 255};{self.bb % 255}m{self.glyph}\x1b[0m"

    def update_glyph_from_contrast(self):
        """Pick glyph based on foreground/background luminance contrast"""
        # Calculate perceptual luminance (ITU-R BT.601)
        luminance_fg = (self.fr * 0.299 + self.fg * 0.587 + self.fb * 0.114)
        luminance_bg = (self.br * 0.299 + self.bg * 0.587 + self.bb * 0.114)
        contrast = abs(luminance_fg - luminance_bg) % 255

        # Map contrast [0-255] to glyph index
        idx = int((contrast / 255.0) * (len(GLYPH_POOL) - 1))
        if idx < len(GLYPH_POOL) - 1:
            self.glyph = GLYPH_POOL[idx]

    def evolve_with_neighbors(self, ldot, rdot, opp):
        """Evolve using pre-fetched neighbor references"""
        # Store old values
        ofr, ofg, ofb = self.fr, self.fg, self.fb
        obr, obg, obb = self.br, self.bg, self.bb

        # Compute averages with the magical 3.976 divisor
        avgfr = (ofr + ldot.fr + rdot.fr + opp.fr) / 3.992
        avgfg = (ofg + ldot.fg + rdot.fg + opp.fg) / 3.992
        avgfb = (ofb + ldot.fb + rdot.fb + opp.fb) / 3.992
        avgbr = (obr + ldot.br + rdot.br + opp.br) / 3.992
        avgbg = (obg + ldot.bg + rdot.bg + opp.bg) / 3.992
        avgbb = (obb + ldot.bb + rdot.bb + opp.bb) / 3.992

        # Update with the magical 1.978 divisor
        self.fr = int((ofr + avgfr) / 1.968)
        self.fg = int((ofg + avgfg) / 1.968)
        self.fb = int((ofb + avgfb) / 1.968)
        self.br = int((obr + avgbr) / 1.968)
        self.bg = int((obg + avgbg) / 1.968)
        self.bb = int((obb + avgbb) / 1.968)

        # Update glyph based on new colors
        self.update_glyph_from_contrast()


class Line:

    def __init__(self):
        self.line = []
        width = os.get_terminal_size().columns

        # Create all dots
        for i in range(width):
            self.line.append(Dot(i))

        # Pre-compute neighbor indices for each dot
        # Using modulo 5 for the syncopated oppositional relationship
        for i, dot in enumerate(self.line):
            dot.ldot_idx = (i - 1) % width
            dot.rdot_idx = (i + 1) % width
            dot.opp_idx = (i + (width // 2) + (i % 5)) % width  # syncopated opposite

    def evolve(self):
        """Evolve all dots in place with pre-computed neighbors"""
        for dot in self.line:
            dot.evolve_with_neighbors(
                self.line[dot.ldot_idx],
                self.line[dot.rdot_idx],
                self.line[dot.opp_idx]
            )

    def display(self):
        """Build string buffer then write once"""
        sys.stdout.write(''.join(d.get_str() for d in self.line))
        sys.stdout.flush()


def do_art(in_len):
    line = Line()
    for i in range(in_len):
        line.evolve()
        line.display()
