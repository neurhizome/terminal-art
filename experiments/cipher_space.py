#!/usr/bin/env python3
"""
cipher_space.py - Negative space walkers carve Lissajous paths through density

The terminal begins filled with dense Unicode texture: a fog of symbols.
Walkers following precise mathematical curves — Lissajous figures — move
through this fog, erasing texture as they pass.

What remains is defined entirely by absence: the paths are visible only
because of what the walkers removed. The art is the negative space.

This is the visual cipher tradition: meaning through emptiness, form through
erasure. The curves are deterministic and beautiful. The texture they carve
through is random. The tension between order and noise is the content.

Lissajous figures arise from two perpendicular harmonic oscillations:
    x(t) = A · sin(a·t + δ)
    y(t) = B · sin(b·t)

Integer ratios a:b produce closed figures. Irrational ratios produce dense
space-filling paths. The phase offset δ transforms circles into ellipses,
figure-eights into Lemniscates of Bernoulli.

This experiment uses the LissajousOrbit behavior from the modular toolkit.
Multiple walkers trace curves with different frequency ratios and phases,
each leaving a distinct carved channel through the background fog.

Usage:
    python3 experiments/cipher_space.py
    python3 experiments/cipher_space.py --walkers 6 --texture dots
    python3 experiments/cipher_space.py --ratios 3,2 5,4 7,4 --delay 0.02
    python3 experiments/cipher_space.py --regenerate 300
"""

import sys
import os
import time
import math
import random
import argparse
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.automata import Walker, Spawner, LissajousOrbit
from src.genetics import Genome
from src.renderers.terminal_stage import TerminalStage


# ---------------------------------------------------------------------------
# Texture palettes — what fills the background
# ---------------------------------------------------------------------------

TEXTURES = {
    'dense':   '░▒▓▒░▒░▓▒░',
    'dots':    '·∘•◦∙○◉●∙·',
    'braille': '⣿⣷⣦⣄⡀⠄⠂⠁⠀',
    'zen':     '∵∴∷⁚∶⁖⸬⁘⁙',
    'runes':   '⊕⊗⊘⊙⊚⊛⊜⊝',
    'math':    '∞∮∯∰∱∲∳∴∵',
}


# ---------------------------------------------------------------------------
# Colour helpers (HSV → ANSI truecolor)
# ---------------------------------------------------------------------------

def _hsv_to_rgb(h: float, s: float = 0.75, v: float = 0.7):
    h6 = h * 6.0
    i  = int(h6)
    f  = h6 - i
    p  = v * (1.0 - s)
    q  = v * (1.0 - f * s)
    t  = v * (1.0 - (1.0 - f) * s)
    sectors = [(v, t, p), (q, v, p), (p, v, t),
               (p, q, v), (t, p, v), (v, p, q)]
    r, g, b = sectors[i % 6]
    return int(r * 255), int(g * 255), int(b * 255)

RESET = '\x1b[0m'


# ---------------------------------------------------------------------------
# Background fog
# ---------------------------------------------------------------------------

class FogGrid:
    """
    2D grid of texture characters. Walkers erase cells to empty space.
    The fog can be regenerated periodically for repeated reveal cycles.
    """

    def __init__(self, width: int, height: int, texture: str):
        self.width   = width
        self.height  = height
        self.texture = texture
        self._cells: list  = []
        self._erased: list = []
        self.regenerate()

    def regenerate(self):
        """Fill grid with random texture characters."""
        chars = list(self.texture)
        self._cells  = [
            [random.choice(chars) for _ in range(self.width)]
            for _ in range(self.height)
        ]
        # Track erased positions: True = erased (blank), False = texture
        self._erased = [
            [False] * self.width
            for _ in range(self.height)
        ]

    def erase(self, x: int, y: int):
        """Erase cell at (x, y) — walker passed through here."""
        if 0 <= x < self.width and 0 <= y < self.height:
            self._erased[y][x] = True

    def char_at(self, x: int, y: int) -> str:
        if 0 <= x < self.width and 0 <= y < self.height:
            if self._erased[y][x]:
                return ' '
            return self._cells[y][x]
        return ' '

    def erased_fraction(self) -> float:
        total   = self.width * self.height
        erased  = sum(self._erased[y][x]
                      for y in range(self.height)
                      for x in range(self.width))
        return erased / total if total > 0 else 0.0


# ---------------------------------------------------------------------------
# Main experiment
# ---------------------------------------------------------------------------

def parse_ratios(ratio_strings):
    """Parse ['3,2', '5,4'] → [(3, 2), (5, 4)]."""
    result = []
    for s in ratio_strings:
        try:
            a, b = map(float, s.split(','))
            result.append((a, b))
        except ValueError:
            pass
    return result or [(3, 2), (5, 4), (7, 4), (2, 3)]


def main():
    parser = argparse.ArgumentParser(
        description='Negative space: Lissajous walkers carve paths through texture fog'
    )
    parser.add_argument('--walkers', type=int, default=4,
                        help='Number of Lissajous walkers')
    parser.add_argument('--texture', choices=list(TEXTURES.keys()),
                        default='dense',
                        help='Background texture palette')
    parser.add_argument('--ratios', nargs='+', default=None,
                        metavar='A,B',
                        help='Frequency ratios for walkers (e.g. 3,2 5,4)')
    parser.add_argument('--speed', type=float, default=0.04,
                        help='Lissajous parameter increment per tick')
    parser.add_argument('--delay', type=float, default=0.03,
                        help='Seconds between frames')
    parser.add_argument('--regenerate', type=int, default=400,
                        help='Regenerate fog after N ticks (0 = never)')
    parser.add_argument('--seed', type=int, default=None)
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    with TerminalStage() as stage:
        width, height = stage.width, stage.height
        texture_chars = TEXTURES[args.texture]
        fog           = FogGrid(width, height, texture_chars)

        # Parse or generate frequency ratios
        ratios = parse_ratios(args.ratios) if args.ratios else []
        # Fill remaining walkers with interesting ratios
        default_ratios = [(3, 2), (5, 4), (7, 4), (2, 3), (5, 3), (4, 3), (7, 6)]
        while len(ratios) < args.walkers:
            ratios.append(default_ratios[len(ratios) % len(default_ratios)])

        # Build walkers — each traces a different Lissajous curve
        behaviors = []
        walkers   = []

        for i in range(args.walkers):
            a, b    = ratios[i % len(ratios)]
            delta   = (i / args.walkers) * math.pi   # spread phases

            hue     = i / args.walkers
            genome  = Genome(
                color_h    = hue,
                saturation = 0.85,
                value      = 0.95,
                vigor      = 1.0,
            )

            behavior = LissajousOrbit(
                a      = a,
                b      = b,
                delta  = delta,
                width  = width,
                height = height,
                speed  = args.speed + random.uniform(-0.005, 0.005),
            )

            walker = Walker(
                x      = width  // 2,
                y      = height // 2,
                genome = genome,
                char   = '·',
            )
            behaviors.append(behavior)
            walkers.append(walker)

        tick = 0

        try:
            while True:
                # === UPDATE ===

                # Move each walker along its Lissajous curve and erase fog
                for walker, behavior in zip(walkers, behaviors):
                    dx, dy = behavior.get_move(
                        walker.x, walker.y,
                        width=width, height=height
                    )
                    walker.move(dx, dy, width, height, wrap=False)

                    # Erase a small brush area around walker position
                    for bx in range(walker.x - 1, walker.x + 2):
                        for by in range(walker.y - 1, walker.y + 2):
                            fog.erase(bx, by)

                # Regenerate fog periodically if requested
                if args.regenerate > 0 and tick > 0 and tick % args.regenerate == 0:
                    fog.regenerate()

                # === RENDER ===

                stage.clear()

                # Background: texture fog (dim)
                for fy in range(height):
                    for fx in range(width):
                        ch = fog.char_at(fx, fy)
                        if ch != ' ':
                            # Dim texture: dark grey
                            stage.cells[fy][fx].char     = ch
                            stage.cells[fy][fx].fg_color = (45, 45, 60)

                # Walkers: bright coloured tips of the carving curves
                for walker in walkers:
                    if 0 <= walker.x < width and 0 <= walker.y < height:
                        r, g, b = walker.genome.to_rgb()
                        stage.cells[walker.y][walker.x].char     = '◉'
                        stage.cells[walker.y][walker.x].fg_color = (r, g, b)

                stage.render_diff()

                # Status bar
                erased_pct = fog.erased_fraction() * 100
                ratio_str  = '  '.join(f'{a:.0f}:{b:.0f}' for a, b in ratios[:args.walkers])
                status = (
                    f' cipher_space  walkers: {args.walkers}'
                    f'  texture: {args.texture}'
                    f'  ratios: {ratio_str}'
                    f'  erased: {erased_pct:.0f}%'
                    f'  ^C quit'
                )
                sys.stdout.write(f'\x1b[{height + 1};1H{status[:width - 1]}\x1b[K')
                sys.stdout.flush()

                time.sleep(args.delay)
                tick += 1

        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
