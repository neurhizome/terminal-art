#!/usr/bin/env python3

from random import randint
import os
import sys

# Import our curated glyph sets
sys.path.insert(0, '/root/colors/colorfalls')
from asciicology_glyphs import (
    HEXAGRAMS, BRAILLE_BY_DENSITY,
    create_contrast_map
)

# Create contrast mapping with 14 levels for fine gradation
GLYPH_HEXAGRAMS = create_contrast_map(HEXAGRAMS, 14)
GLYPH_BRAILLE = create_contrast_map(BRAILLE_BY_DENSITY, 14)

class Dot:

    def __init__(self, idx, use_braille=False):
        self.idx = idx
        self.fr = randint(0,255)
        self.fg = randint(0,255)
        self.fb = randint(0,255)
        self.br = randint(0,255)
        self.bg = randint(0,255)
        self.bb = randint(0,255)

        # Choose glyph set (positive/negative space)
        self.glyph_pool = GLYPH_BRAILLE if use_braille else GLYPH_HEXAGRAMS
        self.glyph = self.glyph_pool[randint(0, len(self.glyph_pool)-1)]

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
        contrast = abs(luminance_fg - luminance_bg)

        # Map contrast [0-255] to glyph index
        idx = int((contrast / 255.0) * (len(self.glyph_pool) - 1)) % len(self.glyph_pool) - 1
        self.glyph = self.glyph_pool[idx]

    def evolve_with_neighbors(self, ldot, rdot, opp, magic_divisor=1.990):
        """Evolve using pre-fetched neighbor references"""
        # Store old values
        ofr, ofg, ofb = self.fr, self.fg, self.fb
        obr, obg, obb = self.br, self.bg, self.bb

        # Compute averages with the magical 3.990 divisor
        avgfr = (ofr + ldot.fr + rdot.fr + opp.fr) / 3.990
        avgfg = (ofg + ldot.fg + rdot.fg + opp.fg) / 3.990
        avgfb = (ofb + ldot.fb + rdot.fb + opp.fb) / 3.990
        avgbr = (obr + ldot.br + rdot.br + opp.br) / 3.990
        avgbg = (obg + ldot.bg + rdot.bg + opp.bg) / 3.990
        avgbb = (obb + ldot.bb + rdot.bb + opp.bb) / 3.990

        # Update with the tunable magic divisor
        self.fr = int((ofr + avgfr) / magic_divisor)
        self.fg = int((ofg + avgfg) / magic_divisor)
        self.fb = int((ofb + avgfb) / magic_divisor)
        self.br = int((obr + avgbr) / magic_divisor)
        self.bg = int((obg + avgbg) / magic_divisor)
        self.bb = int((obb + avgbb) / magic_divisor)

        # Update glyph based on new colors
        self.update_glyph_from_contrast()


class Line:

    def __init__(self, use_braille=False, syncopation=5):
        self.line = []
        width = os.get_terminal_size().columns
        self.syncopation = syncopation

        # Create all dots
        for i in range(width):
            self.line.append(Dot(i, use_braille=use_braille))

        # Pre-compute neighbor indices for each dot
        for i, dot in enumerate(self.line):
            dot.ldot_idx = (i - 1) % width
            dot.rdot_idx = (i + 1) % width
            # Syncopated oppositional relationship
            dot.opp_idx = (i + (width // 2) + (i % syncopation)) % width

    def evolve(self, magic_divisor=1.990):
        """Evolve all dots in place with pre-computed neighbors"""
        for dot in self.line:
            dot.evolve_with_neighbors(
                self.line[dot.ldot_idx],
                self.line[dot.rdot_idx],
                self.line[dot.opp_idx],
                magic_divisor=magic_divisor
            )

    def display(self):
        """Build string buffer then write once"""
        sys.stdout.write(''.join(d.get_str() for d in self.line))
        sys.stdout.flush()


def do_art(in_len, use_braille=False, syncopation=5, magic_divisor=1.990):
    """
    Generate asciicology art

    Args:
        in_len: Number of lines to generate
        use_braille: If True, use Braille patterns (negative space)
                    If False, use I Ching hexagrams (positive space)
        syncopation: Modulo value for oppositional relationships (1-7 recommended)
        magic_divisor: Tunable decay parameter (1.990-1.995 for coherence)
    """
    line = Line(use_braille=use_braille, syncopation=syncopation)
    for i in range(in_len):
        line.evolve(magic_divisor=magic_divisor)
        line.display()


def do_dual_art(in_len, syncopation=5, magic_divisor=1.990):
    """
    Generate dual-layer art: hexagrams AND braille overlaid
    (Warning: terminal may not render combining characters well)
    """
    line_hexa = Line(use_braille=False, syncopation=syncopation)
    line_braille = Line(use_braille=True, syncopation=syncopation)

    for i in range(in_len):
        line_hexa.evolve(magic_divisor=magic_divisor)
        line_braille.evolve(magic_divisor=magic_divisor)

        # Alternate lines between the two systems
        if i % 2 == 0:
            line_hexa.display()
        else:
            line_braille.display()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Asciicology - Generative Terminal Art')
    parser.add_argument('lines', type=int, nargs='?', default=100,
                       help='Number of lines to generate (default: 100)')
    parser.add_argument('--braille', action='store_true',
                       help='Use Braille patterns instead of hexagrams')
    parser.add_argument('--dual', action='store_true',
                       help='Alternate between hexagrams and Braille')
    parser.add_argument('--sync', type=int, default=5,
                       help='Syncopation modulo (default: 5)')
    parser.add_argument('--magic', type=float, default=1.990,
                       help='Magic divisor for tuning coherence (default: 1.990)')

    args = parser.parse_args()

    if args.dual:
        do_dual_art(args.lines, syncopation=args.sync, magic_divisor=args.magic)
    else:
        do_art(args.lines, use_braille=args.braille,
               syncopation=args.sync, magic_divisor=args.magic)
