#!/usr/bin/env python3
"""
entropy_staircase.py — friend.py's divisors, driven by a real mind settling.

A lens specimen (homelab/lens) records full-vocabulary entropy at every
layer of gemma4-e2b as it reads one token position. Early and mid layers
hover at 9-14 bits — the model is still churning. The last eight layers
collapse: 7.65 → 3.67 → 1.4 → 0.0. The answer arrives.

Session 008 established what friend.py's divisors mean: below the neutral
values (4.0, 2.0) the line amplifies and lives; above them it damps toward
the neighborhood mean — gray, equilibrium, the death of the pattern.

So: map each layer's measured entropy onto the divisor interval

    avg_div(e) = 4.008 - (4.008 - 3.759) * (e / e_max)
    upd_div(e) = 2.008 - (2.008 - 1.986) * (e / e_max)

At the specimen's hottest layer (e_max, self-normalized) the arithmetic is
exactly friend.py's evolve — maximum aliveness. At entropy zero it is
friend.py's devolve — settling. Nothing else is invented: the entire
temporal structure of the piece is the measurement.

Run K steps per layer, shallow to deep, one row per step. The color waves
churn through the mid-band and then — because the model stopped being
uncertain — the line goes still. The glyph per row is the entropy band
(█▓▒░·): glyph weather, coarse-grained.

Run from terminal-art root:
  python3 experiments/entropy_staircase.py                # live render
  python3 experiments/entropy_staircase.py --capture out.ans
  python3 experiments/entropy_staircase.py --specimen /path/to/specimen.json
"""

import argparse
import json
import os
import random
import sys

DEFAULT_SPECIMEN = (
    "/mnt/activations/lens/gemma4-e2b/specimens/2026-07-10/"
    "20260710T194300-65543966.json"
)

# Session 008's constants: the living interval around neutral.
ALIVE_AVG, ALIVE_UPD = 3.759, 1.986   # evolve — amplifying
STILL_AVG, STILL_UPD = 4.008, 2.008   # devolve — damping

GLYPH_BANDS = "·░▒▓█"  # entropy 0 → e_max, coarse-grained glyph weather


def load_staircase(path, position=-1):
    """Entropy per layer (bits) at one captured position, shallow→deep."""
    with open(path) as f:
        d = json.load(f)
    ll = d["channels"]["logit_lens"]
    ent = ll["entropy"]  # [n_layers][seq_len]
    pos = position if position >= 0 else len(ent[0]) + position
    return d["id"], [ent[i][pos] for i in range(len(ent))]


def divisors_for(e, e_max):
    t = max(0.0, min(1.0, e / e_max))
    return (
        STILL_AVG - (STILL_AVG - ALIVE_AVG) * t,
        STILL_UPD - (STILL_UPD - ALIVE_UPD) * t,
    )


class Dot:
    __slots__ = ("fr", "fg", "fb", "br", "bg", "bb")

    def __init__(self, rng):
        self.fr, self.fg, self.fb = (rng.randint(0, 255) for _ in range(3))
        self.br, self.bg, self.bb = (rng.randint(0, 255) for _ in range(3))

    def render(self, glyph):
        return (
            f"\x1b[38;2;{self.fr % 255};{self.fg % 255};{self.fb % 255}m"
            f"\x1b[48;2;{self.br % 255};{self.bg % 255};{self.bb % 255}m"
            f"{glyph}\x1b[0m"
        )

    def step(self, ldot, rdot, opp, avg_div, upd_div):
        ofr, ofg, ofb = self.fr, self.fg, self.fb
        obr, obg, obb = self.br, self.bg, self.bb
        avgfr = (ofr + ldot.fr + rdot.fr + opp.br) / avg_div
        avgfg = (ofg + ldot.fg + rdot.fg + opp.bg) / avg_div
        avgfb = (ofb + ldot.fb + rdot.fb + opp.bb) / avg_div
        avgbr = (obr + ldot.br + rdot.br + opp.fr) / avg_div
        avgbg = (obg + ldot.bg + rdot.bg + opp.fg) / avg_div
        avgbb = (obb + ldot.bb + rdot.bb + opp.fb) / avg_div
        self.fr = int((ofr + avgfr) / upd_div)
        self.fg = int((ofg + avgfg) / upd_div)
        self.fb = int((ofb + avgfb) / upd_div)
        self.br = int((obr + avgbr) / upd_div)
        self.bg = int((obg + avgbg) / upd_div)
        self.bb = int((obb + avgbb) / upd_div)


def run(specimen, position, steps_per_layer, width, out):
    sid, stairs = load_staircase(specimen, position)
    e_max = max(stairs)
    rng = random.Random(sid)  # deterministic: the specimen is the seed

    dots = [Dot(rng) for _ in range(width)]
    lidx = [(i - 1) % width for i in range(width)]
    ridx = [(i + 1) % width for i in range(width)]
    oidx = [abs(width - 1 - i) for i in range(width)]

    lines = []
    for layer, e in enumerate(stairs):
        avg_div, upd_div = divisors_for(e, e_max)
        glyph = GLYPH_BANDS[min(len(GLYPH_BANDS) - 1,
                                int(e / e_max * len(GLYPH_BANDS)))]
        for _ in range(steps_per_layer):
            for i, dot in enumerate(dots):
                dot.step(dots[lidx[i]], dots[ridx[i]], dots[oidx[i]],
                         avg_div, upd_div)
            row = "".join(d.render(glyph) for d in dots)
            lines.append(f"{row}  \x1b[2mL{layer:02d} {e:5.2f}b\x1b[0m")

    text = "\n".join(lines) + "\n"
    if out:
        with open(out, "w") as f:
            f.write(text)
        print(f"wrote {len(lines)} rows to {out}  (specimen {sid}, "
              f"e_max {e_max:.2f}b at self-normalized ceiling)")
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--specimen", default=DEFAULT_SPECIMEN)
    ap.add_argument("--position", type=int, default=-1,
                    help="captured token position (default: last)")
    ap.add_argument("--steps", type=int, default=4,
                    help="automaton steps per layer")
    ap.add_argument("--width", type=int, default=0,
                    help="cells per row (default: terminal width - 12)")
    ap.add_argument("--capture", default=None, help="write .ans to path")
    args = ap.parse_args()
    width = args.width or max(40, os.get_terminal_size().columns - 12)
    run(args.specimen, args.position, args.steps, width, args.capture)
