#!/usr/bin/env python3

# cosmic_field.py

# 

# An excitable medium where unicode glyphs exist in
# energy states.

# Excited cells trigger neighbors, creating cascading
# spirals and collapses.

# Braille patterns, combining accents, and other unicode
# form the "particles."

# 

# Examples:

# python3 cosmic_field.py –rows 1000 –delay 0.015

# python3 cosmic_field.py –spark_rate 0.08
# –excite_threshold 2.5

# python3 cosmic_field.py –gravity 0.85 –seed 42

import argparse import random import shutil import sys
import time import math import colorsys from dataclasses
import dataclass from typing import List, Tuple

# —————————– Glyph Energy Levels —————————–

# Each level has glyphs that represent different energy
# states

# Lower index = lower energy (dim/sparse) → Higher index
# = higher energy (bright/dense)

ENERGY_GLYPHS = [
        # Level 0: Nearly empty space
        [" ", "·", "∙", "·"],
        # Level 1: Faint stirring
        ["⠀", "⠁", "⠂", "⠄", "⠈", "⠐", "⠠"],
        # Level 2: Awakening braille
        ["⡀", "⢀", "⠃", "⠅", "⠉", "⠑", "⠡", "⢁", "⡁"],
        # Level 3: Active particles
        ["⠇", "⠏", "⠟", "⠿", "⡇", "⡏", "⢇", "⢏", "⣇",
            "⣏"],
        # Level 4: Dense clusters
        ["⣿", "⣾", "⣽", "⣻", "⣯", "⣷", "◦", "○", "◉",
            "●"],
        # Level 5: Maximum energy - combining characters
        # create "thick" glyphs
        ["⣿̈", "⣿̊", "⣿⃝", "◉̈", "●̊", "✦", "✧", "⁕", "⁜",
            "∴", "∵", "⋮", "⋯"],
        # Level 6: Supernova / collapse precursor
        ["◉̈⃝", "⁂", "✶", "✷", "❋", "✸", "✹", "⁕⃝", "※",
            "٭", "⁎"],
        # Level 7: Collapse/rebirth
        ["◌", "○", "◯", "", "◦", "∘"] ]

def glyph_for_energy(energy: float) -> str: """Map
continuous energy [0, inf) to a glyph."""
    # Collapse high energies back down (creates the
    # spiral/collapse effect)
    if energy > 7.5:
        # Oscillate through collapse states
        cycle = int(energy) % len(ENERGY_GLYPHS[-1])
        return ENERGY_GLYPHS[-1][cycle]

level = int(energy) level = max(0, min(level,
    len(ENERGY_GLYPHS) - 1)) glyphs =
ENERGY_GLYPHS[level] return random.choice(glyphs) if
glyphs else " "

# —————————– Color Mapping —————————–

def energy_to_color(energy: float, base_hue: float) ->
Tuple[Tuple[int,int,int], Tuple[int,int,int]]: """Map
energy to fg/bg color pair. Higher energy = more
vibrant/shifted hue."""
# Normalize energy for color mapping
e_norm = min(energy / 8.0, 1.0)

# Hue shifts with energy (spiral through spectrum)
hue = (base_hue + e_norm * 0.3) % 1.0

# Saturation and value increase with energy
sat = 0.3 + 0.7 * e_norm val = 0.4 + 0.6 * e_norm

# Foreground
rf, gf, bf = colorsys.hsv_to_rgb(hue, sat, val) fg =
(int(rf*255), int(gf*255), int(bf*255))

# Background: complementary but darker
bg_hue = (hue + 0.5) % 1.0
bg_sat = 0.3 + 0.3 * (1.0 - e_norm)
bg_val = 0.15 + 0.15 * (1.0 - e_norm)
rb, gb, bb = colorsys.hsv_to_rgb(bg_hue, bg_sat, bg_val)
bg = (int(rb*255), int(gb*255), int(bb*255))

return fg, bg

# —————————– Excitable Medium Physics —————————–

def compute_excitation(cells: List[float], i: int, neighbors: int,
        excite_threshold: float, diffusion: float) -> float:
    """
Compute how much a cell gets excited by its neighbors.
Returns the excitation contribution (added to cell’s energy).
"""
left = cells[(i - 1) % len(cells)]
right = cells[(i + 1) % len(cells)]

# Count highly excited neighbors
excited_neighbors = 0
neighbor_energy = 0.0

for ne in [left, right]:
    if ne > excite_threshold:
        excited_neighbors += 1
        neighbor_energy += ne

if excited_neighbors == 0:
    return 0.0

# Excitation spreads from excited neighbors
# More excited neighbors = stronger effect
excitation = (neighbor_energy / neighbors) * diffusion * 0.3

return excitation

def update_field(cells: List[float], base_hues: List[float],
        excite_threshold: float, diffusion: float,
        decay: float, gravity: float, spark_rate: float) -> Tuple[List[float], List[float]]:
    """
Update the excitable medium field for one time step.

Physics:
    - Excited cells (> threshold) can trigger neighbors
- Energy naturally decays
- Gravity pulls high energy back down (collapse)
- Random sparks seed new excitations
"""
n = len(cells)
new_cells = [0.0] * n
new_hues = list(base_hues)

for i in range(n):
    current = cells[i]

    # 1. Decay
    energy = current * decay

    # 2. Excitation from neighbors
    excitation = compute_excitation(cells, i, 2, excite_threshold, diffusion)
    energy += excitation

    # 3. Gravity/collapse for very high energies
    if energy > 7.0:
        # Pull it back down, but with momentum (doesn't go to 0 immediately)
        energy = energy * gravity + (1.0 - gravity) * random.uniform(0.5, 2.0)

    # 4. Random sparks
    if random.random() < spark_rate:
        energy += random.uniform(1.5, 4.0)
        # Shift hue on spark
        new_hues[i] = (base_hues[i] + random.uniform(-0.1, 0.1)) % 1.0

    # 5. Hue diffusion (colors bleed between neighbors)
    if excitation > 0:
        left_hue = base_hues[(i-1) % n]
        right_hue = base_hues[(i+1) % n]
        # Circular mean of hues
        hues = [left_hue, base_hues[i], right_hue]
        cos_sum = sum(math.cos(2*math.pi*h) for h in hues)
        sin_sum = sum(math.sin(2*math.pi*h) for h in hues)
        new_hues[i] = (math.atan2(sin_sum, cos_sum) / (2*math.pi)) % 1.0

    new_cells[i] = max(0.0, energy)

return new_cells, new_hues

# —————————– Rendering —————————–

def render_line(cells: List[float], base_hues: List[float]) -> str:
    """Render one line of the field."""
parts = []
for i, energy in enumerate(cells):
    glyph = glyph_for_energy(energy)
fg, bg = energy_to_color(energy, base_hues[i])

    fr, fg_g, fb = fg
    br, bg_g, bb = bg

    part = f"\x1b[38;2;{fr};{fg_g};{fb}m\x1b[48;2;{br};{bg_g};{bb}m{glyph}\x1b[0m"
    parts.append(part)

return "".join(parts)

# —————————– Main —————————–

def main():
    ap = argparse.ArgumentParser(description="Excitable unicode glyph field simulation")
ap.add_argument("–rows", type=int, default=0, help="Number of rows to generate (0=infinite)")
ap.add_argument("–delay", type=float, default=0.02, help="Seconds between frames")
ap.add_argument("–seed", type=int, default=None, help="Random seed")
ap.add_argument("–excite_threshold", type=float, default=2.8,
        help="Energy threshold for exciting neighbors")
ap.add_argument("–diffusion", type=float, default=0.85,
        help="How strongly excited cells affect neighbors")
ap.add_argument("–decay", type=float, default=0.92,
        help="Energy decay per step (0-1)")
ap.add_argument("–gravity", type=float, default=0.75,
        help="Collapse factor for high energy (0-1)")
ap.add_argument("–spark_rate", type=float, default=0.04,
        help="Probability of random spark per cell")

args = ap.parse_args()

if args.seed is not None:
    random.seed(args.seed)

# UTF-8 output
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# Initialize field
term_cols = max(1, shutil.get_terminal_size(fallback=(80, 24)).columns)
cells = [random.uniform(0.0, 3.0) for _ in range(term_cols)]
base_hues = [random.random() for _ in range(term_cols)]

count = 0
try:
    while True:
        # Check for terminal resize
        new_cols = max(1, shutil.get_terminal_size(fallback=(80, 24)).columns)
        if new_cols != term_cols:
            term_cols = new_cols
            cells = (cells[:term_cols] + [random.uniform(0.0, 2.0) 
                for _ in range(max(0, term_cols - len(cells)))])[:term_cols]
            base_hues = (base_hues[:term_cols] + [random.random() 
                for _ in range(max(0, term_cols - len(base_hues)))])[:term_cols]

            # Render current state
        line = render_line(cells, base_hues)
        sys.stdout.write(line + "\n")
        sys.stdout.flush()

        # Update physics
        cells, base_hues = update_field(
                cells, base_hues,
                args.excite_threshold,
                args.diffusion,
                args.decay,
                args.gravity,
                args.spark_rate
                )

        count += 1
        if args.rows and count >= args.rows:
            break

        if args.delay > 0:
            time.sleep(args.delay)

except KeyboardInterrupt:
    pass
finally:
    sys.stdout.write("\x1b[0m\n")
    sys.stdout.flush()

if __name__ == "__main__":
    main()
