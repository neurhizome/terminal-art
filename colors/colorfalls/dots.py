#!/usr/bin/env python3

from random import randint
import os

class Dot:

    def __init__(self, idx):
        self.idx = idx
        self.fr = randint(0,255)
        self.fg = randint(0,255)
        self.fb = randint(0,255)
        self.br = randint(0,255)
        self.bg = randint(0,255)
        self.bb = randint(0,255)
        self.glyph = "▤"

    def get_str(self):
        return f"\x1b[38;2;{self.fr};{self.fg};{self.fb}m\x1b[48;2;{self.br};{self.bg};{self.bb}m{self.glyph}\x1b[0m"

    def evolve(self, in_line):
        self.ofr = self.fr
        self.ofg = self.fg
        self.ofb = self.fb
        self.obr = self.br
        self.obg = self.bg
        self.obb = self.bb

        if self.idx != len(in_line.line) - 1:
            self.rdot = in_line.line[self.idx + 1]
            self.opp = in_line.line[abs(len(in_line.line) - 1 - self.idx)]
        elif self.idx == len(in_line.line) - 1:
            self.rdot = in_line.line[0]
            self.opp = in_line.line[abs(len(in_line.line) - 1 - self.idx)]
        if self.idx != 0:
            self.ldot = in_line.line[self.idx - 1]
            self.opp = in_line.line[abs(len(in_line.line) - 1 - self.idx)]
        elif self.idx == 0:
            self.ldot = in_line.line[-1]
            self.opp = in_line.line[abs(len(in_line.line) - 1 - self.idx)]

        self.avgfr = (self.ofr + self.ldot.fr + self.rdot.fr + self.opp.fr) / 3.988
        self.avgfg = (self.ofg + self.ldot.fg + self.rdot.fg + self.opp.fg) / 3.988
        self.avgfb = (self.ofb + self.ldot.fb + self.rdot.fb + self.opp.fb) / 3.988
        self.avgbr = (self.obr + self.ldot.br + self.rdot.br + self.opp.br) / 3.988
        self.avgbg = (self.obg + self.ldot.bg + self.rdot.bg + self.opp.bg) / 3.988
        self.avgbb = (self.obb + self.ldot.bb + self.rdot.bb + self.opp.bb) / 3.988

        self.fr = int((self.ofr + self.avgfr) / 1.988)
        self.fg = int((self.ofg + self.avgfg) / 1.988)
        self.fb = int((self.ofb + self.avgfb) / 1.988)
        self.br = int((self.obr + self.avgbr) / 1.988)
        self.bg = int((self.obg + self.avgbg) / 1.988)
        self.bb = int((self.obb + self.avgbb) / 1.988)

        return(self)

class Line:

    def __init__(self):
        self.line = []
        for i in range(os.get_terminal_size().columns):
            self.line.append(Dot(i))

    def display(self):
        for d in self.line:
            print(f"{d.get_str()}", end="")

def do_art(in_len):
    line = Line()
    for i in range(in_len):
        for d in line.line:
            d = d.evolve(line)
        line.display()
