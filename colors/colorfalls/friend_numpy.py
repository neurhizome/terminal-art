#!/usr/bin/env python3

import numpy as np
import os
import sys
from random import choice

class OptimizedCrazierLine:
    def __init__(self):
        width = os.get_terminal_size().columns
        self.width = width
        self.fr = np.random.randint(0, 256, width)
        self.fg = np.random.randint(0, 256, width)
        self.fb = np.random.randint(0, 256, width)
        self.br = np.random.randint(0, 256, width)
        self.bg = np.random.randint(0, 256, width)
        self.bb = np.random.randint(0, 256, width)
        self.glyphs = np.array([choice(['☼', '★', '◉', '◆', '█', '▓', '▒', '░']) for _ in range(width)])
        
        self.ldot = np.roll(np.arange(width), 1)
        self.rdot = np.roll(np.arange(width), -1)
        self.opp = np.abs(width - 1 - (np.arange(width) % 7))  # Crazier opp: modulo 7 for more asymmetry
        
        self.noise_factor = 0.05  # Gaussian noise scaled by value magnitude for amplifying chaos

    def evolve(self):
        ofr, ofg, ofb = self.fr.copy(), self.fg.copy(), self.fb.copy()
        obr, obg, obb = self.br.copy(), self.bg.copy(), self.bb.copy()
        
        l_fr, l_fg, l_fb = self.fr[self.ldot], self.fg[self.ldot], self.fb[self.ldot]
        r_fr, r_fg, r_fb = self.fr[self.rdot], self.fg[self.rdot], self.fb[self.rdot]
        opp_br, opp_bg, opp_bb = self.br[self.opp], self.bg[self.opp], self.bb[self.opp]
        
        l_br, l_bg, l_bb = self.br[self.ldot], self.bg[self.ldot], self.bb[self.ldot]
        r_br, r_bg, r_bb = self.br[self.rdot], self.bg[self.rdot], self.bb[self.rdot]
        opp_fr, opp_fg, opp_fb = self.fr[self.opp], self.fg[self.opp], self.fb[self.opp]
        
        avgfr = (ofr + l_fr + r_fr + opp_br) / 3.976
        avgfg = (ofg + l_fg + r_fg + opp_bg) / 3.976
        avgfb = (ofb + l_fb + r_fb + opp_bb) / 3.976
        avgbr = (obr + l_br + r_br + opp_fr) / 3.976
        avgbg = (obg + l_bg + r_bg + opp_fg) / 3.976
        avgbb = (obb + l_bb + r_bb + opp_fb) / 3.976
        
        self.fr = ((ofr + avgfr) / 1.989 + np.random.normal(0, self.noise_factor * np.abs(ofr), self.width)).astype(int)
        self.fg = ((ofg + avgfg) / 1.989 + np.random.normal(0, self.noise_factor * np.abs(ofg), self.width)).astype(int)
        self.fb = ((ofb + avgfb) / 1.989 + np.random.normal(0, self.noise_factor * np.abs(ofb), self.width)).astype(int)
        self.br = ((obr + avgbr) / 1.989 + np.random.normal(0, self.noise_factor * np.abs(obr), self.width)).astype(int)
        self.bg = ((obg + avgbg) / 1.989 + np.random.normal(0, self.noise_factor * np.abs(obg), self.width)).astype(int)
        self.bb = ((obb + avgbb) / 1.989 + np.random.normal(0, self.noise_factor * np.abs(obb), self.width)).astype(int)
        
        mutate_prob = 0.01  # 1% chance to mutate glyph per cell per step
        mutations = np.random.rand(self.width) < mutate_prob
        if mutations.any():
            self.glyphs[mutations] = [choice(['☼', '★', '◉', '◆', '█', '▓', '▒', '░']) for _ in range(mutations.sum())]

    def display(self):
        parts = []
        for i in range(self.width):
            fr, fg, fb = self.fr[i] % 243, self.fg[i] % 255, self.fb[i] % 234
            br, bg, bb = self.br[i] % 234, self.bg[i] % 255, self.bb[i] % 243
            parts.append(f"\x1b[38;2;{fr};{fg};{fb}m\x1b[48;2;{br};{bg};{bb}m{self.glyphs[i]}\x1b[0m")
        sys.stdout.write(''.join(parts))
        sys.stdout.flush()

def do_art(in_len):
    line = OptimizedCrazierLine()
    for i in range(in_len):
        line.evolve()
        line.display()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        do_art(int(sys.argv[1]))
    else:
        do_art(100)  # Default to 100 rows if no arg provided