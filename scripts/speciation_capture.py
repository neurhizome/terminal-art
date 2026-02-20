#!/usr/bin/env python3
"""
scripts/speciation_capture.py  –  Color speciation timeline: 6 captures.

Runs the color_speciation experiment headlessly and captures frames at
tick [0, 500, 1500, 3000, 5000, 8000].  Each 88×28 two-panel frame:

    ┌─ CHROMATIC SCHISM  tick XXXXX ────────────────────┐┌─ SPECIES ──────┐
    │  territory background + walkers ● (hue-colored)   ││ diversity spark│
    │  61 × 26 inner simulation grid                    ││ lineage bars   │
    └──────────────────────────────────────────────────  ┘└────────────────┘

Output:
    docs/assets/captures/speciation-t0000.ans
    docs/assets/captures/speciation-t0500.ans
    docs/assets/captures/speciation-t1500.ans
    docs/assets/captures/speciation-t3000.ans
    docs/assets/captures/speciation-t5000.ans
    docs/assets/captures/speciation-t8000.ans
"""

import argparse
import colorsys
import random
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.automata import Spawner, RandomWalk
from src.genetics import Genome, circular_distance
from src.fields import TerritoryField

# ── simulation parameters ──────────────────────────────────────────────────────
SEED                = 17
CHECKPOINTS         = [0, 500, 1500, 3000, 5000, 8000]
INITIAL_SPECIES     = 8
WALKERS_PER_SPECIES = 15
MAX_WALKERS         = 400
BREED_THRESHOLD     = 0.15
BREED_RADIUS        = 6.0
SPAWN_RATE          = 0.08
DIV_INTERVAL        = 50

# ── canvas geometry ────────────────────────────────────────────────────────────
TOTAL_W, TOTAL_H = 88, 28
SIM_PANEL_W      = 63            # left panel outer width (borders included)
STATS_PANEL_W    = TOTAL_W - SIM_PANEL_W   # 25
SIM_W            = SIM_PANEL_W - 2         # 61 inner cols
SIM_H            = TOTAL_H - 2            # 26 inner rows

# ── UI colour palette ──────────────────────────────────────────────────────────
BG        = (17,  21,  28)
C_FRAME_L = (160, 100, 220)   # violet  – left panel
C_FRAME_R = (80,  80,  110)   # muted   – right panel
C_HEAD    = (200, 212, 230)
C_DIM     = (66,  78,  100)
C_STAT_H  = (229, 192, 123)   # amber

SPARK_CHARS = ' ▁▂▃▄▅▆▇█'


def _fg(r, g, b): return f"\x1b[38;2;{r};{g};{b}m"
def _bg(r, g, b): return f"\x1b[48;2;{r};{g};{b}m"
RST = "\x1b[0m"


# ── Canvas ────────────────────────────────────────────────────────────────────
class Canvas:
    def __init__(self, cols, rows):
        self.cols, self.rows = cols, rows
        self.ch = [[' '] * cols for _ in range(rows)]
        self.fc = [[None]  * cols for _ in range(rows)]
        self.bc = [[BG]    * cols for _ in range(rows)]

    def put(self, x, y, char, fc=None, bc=None):
        if 0 <= x < self.cols and 0 <= y < self.rows:
            self.ch[y][x] = char
            if fc is not None: self.fc[y][x] = fc
            if bc is not None: self.bc[y][x] = bc

    def txt(self, x, y, s, fc=None, bc=None):
        for i, c in enumerate(s):
            self.put(x + i, y, c, fc, bc)

    def hline(self, x, y, n, c, fc=None):
        for i in range(n): self.put(x + i, y, c, fc)

    def vline(self, x, y, n, c, fc=None):
        for i in range(n): self.put(x, y + i, c, fc)

    def box(self, x, y, w, h, color, style='single', label=None):
        tl, hz, tr, vt, bl, br = {
            'single': ('┌', '─', '┐', '│', '└', '┘'),
            'double': ('╔', '═', '╗', '║', '╚', '╝'),
            'heavy':  ('┏', '━', '┓', '┃', '┗', '┛'),
            'round':  ('╭', '─', '╮', '│', '╰', '╯'),
        }[style]
        self.put(x,     y,     tl, color)
        self.hline(x+1, y,     w-2, hz, color)
        self.put(x+w-1, y,     tr, color)
        self.put(x,     y+h-1, bl, color)
        self.hline(x+1, y+h-1, w-2, hz, color)
        self.put(x+w-1, y+h-1, br, color)
        self.vline(x,     y+1, h-2, vt, color)
        self.vline(x+w-1, y+1, h-2, vt, color)
        if label:
            lbl = f" {label} "
            self.txt(x + 2, y, lbl, fc=color)

    def to_ansi(self):
        out = []
        for row in range(self.rows):
            line = []
            cf = cb = None
            for col in range(self.cols):
                c  = self.ch[row][col]
                nf = self.fc[row][col]
                nb = self.bc[row][col]
                if nf != cf:
                    line.append(_fg(*nf) if nf else "\x1b[39m")
                    cf = nf
                if nb != cb:
                    line.append(_bg(*nb) if nb else "\x1b[49m")
                    cb = nb
                line.append(c)
            out.append(''.join(line))
        return '\r\n'.join(out) + RST


# ── simulation ────────────────────────────────────────────────────────────────
class Simulation:
    def __init__(self, seed=SEED):
        random.seed(seed)
        self.seed       = seed
        self.tick       = 0
        self.spawner    = Spawner(max_walkers=MAX_WALKERS, width=SIM_W, height=SIM_H)
        self.territory  = TerritoryField(SIM_W, SIM_H, chunk_size=8)
        self.behavior   = RandomWalk(eight_way=True)
        self.div_history = []   # species count over time

        for i in range(INITIAL_SPECIES):
            base_hue = i / INITIAL_SPECIES
            for _ in range(WALKERS_PER_SPECIES):
                hue = (base_hue + random.gauss(0, 0.02)) % 1.0
                genome = Genome(
                    color_h=hue,
                    vigor=random.uniform(0.8, 1.2),
                    saturation=0.9,
                    value=0.9,
                )
                self.spawner.spawn_random(genome=genome, char='●')

    def step(self):
        self.spawner.age_all()

        for walker in self.spawner.walkers:
            self.territory.claim(walker)
            dx, dy = self.behavior.get_move(walker.x, walker.y)
            walker.move(dx, dy, SIM_W, SIM_H, wrap=True)

        if not self.spawner.is_full() and random.random() < SPAWN_RATE:
            walker = random.choice(self.spawner.walkers)
            partners = self.spawner.find_breeding_partners(
                walker, BREED_RADIUS, threshold=BREED_THRESHOLD
            )
            if partners:
                partner = random.choice(partners)
                self.spawner.spawn_from_parents(walker, partner, mutation_rate=0.02)

        self.spawner.remove_dead(max_age=800, vigor_threshold=0.2)

        active_ids = {id(w) for w in self.spawner.walkers}
        self.territory.prune_genomes(active_ids)

        if self.tick % DIV_INTERVAL == 0:
            d = _measure_diversity(self.spawner.walkers)
            self.div_history.append(d)
            if len(self.div_history) > 30:
                self.div_history.pop(0)

        self.tick += 1

    def run_to(self, target):
        print(f"  running to tick {target}...", end='', flush=True)
        while self.tick < target:
            self.step()
            if self.tick % 500 == 0:
                print(f" {self.tick}", end='', flush=True)
        print()


# ── helpers ───────────────────────────────────────────────────────────────────
def _measure_diversity(walkers):
    if not walkers:
        return 0
    hues = sorted(w.genome.color_h for w in walkers)
    count = 1
    prev = hues[0]
    for h in hues[1:]:
        if circular_distance(prev, h) > 0.1:
            count += 1
        prev = h
    if len(hues) > 1 and circular_distance(hues[-1], hues[0]) < 0.1:
        count -= 1
    return max(1, count)


def _sparkline(values, width):
    if not values:
        return ' ' * width
    mv = max(values) or 1
    n = len(values)
    if n <= width:
        sampled = values + [0] * (width - n)
    else:
        step = n / width
        sampled = [values[int(i * step)] for i in range(width)]
    return ''.join(
        SPARK_CHARS[max(0, min(int(v / mv * (len(SPARK_CHARS) - 1)),
                               len(SPARK_CHARS) - 1))]
        for v in sampled
    )


def _cluster_species(walkers):
    """Group walkers into hue-clusters; return (rgb, count) list, sorted by hue."""
    if not walkers:
        return []
    by_hue = sorted(walkers, key=lambda w: w.genome.color_h)
    clusters, current = [], [by_hue[0]]
    for w in by_hue[1:]:
        if circular_distance(current[-1].genome.color_h, w.genome.color_h) <= 0.1:
            current.append(w)
        else:
            clusters.append(current)
            current = [w]
    clusters.append(current)
    # wrap-around merge
    if (len(clusters) > 1 and
            circular_distance(clusters[-1][-1].genome.color_h,
                               clusters[0][0].genome.color_h) < 0.1):
        clusters[0] = clusters[-1] + clusters[0]
        clusters.pop()
    result = []
    for cl in clusters:
        mean_h = sum(w.genome.color_h for w in cl) / len(cl)
        r, g, b = colorsys.hsv_to_rgb(mean_h, 0.88, 0.92)
        result.append(((int(r * 255), int(g * 255), int(b * 255)), len(cl)))
    return result


# ── frame renderer ────────────────────────────────────────────────────────────
def render_frame(sim):
    cv = Canvas(TOTAL_W, TOTAL_H)

    # ── left panel: territory + walkers ──────────────────────────────────────
    cv.box(0, 0, SIM_PANEL_W, TOTAL_H, C_FRAME_L, style='double',
           label=f'CHROMATIC SCHISM  tick {sim.tick:05d}')

    ter = sim.territory.render()
    for ry in range(SIM_H):
        for rx in range(SIM_W):
            _char, _fg_col, bg = ter[ry][rx]
            if bg and bg != (0, 0, 0):
                # dim territory colour to 50% so walkers pop
                cv.bc[ry + 1][rx + 1] = (
                    int(bg[0] * 0.50),
                    int(bg[1] * 0.50),
                    int(bg[2] * 0.50),
                )

    for w in sim.spawner.walkers:
        if 0 <= w.x < SIM_W and 0 <= w.y < SIM_H:
            r, g, b = w.genome.to_rgb()
            cv.put(w.x + 1, w.y + 1, '●', fc=(r, g, b))

    # ── right panel: stats ────────────────────────────────────────────────────
    sx = SIM_PANEL_W
    sw = STATS_PANEL_W
    ix = sx + 1          # inner x
    iw = sw - 2          # inner width

    cv.box(sx, 0, sw, TOTAL_H, C_FRAME_R, style='single', label='SPECIES')

    stats   = sim.spawner.get_stats()
    pop     = stats['count']
    cur_d   = sim.div_history[-1]  if sim.div_history else INITIAL_SPECIES
    avg_d   = (sum(sim.div_history) / len(sim.div_history)
               if sim.div_history else float(INITIAL_SPECIES))

    cv.txt(ix, 1, f"pop {pop:3d}/{MAX_WALKERS}", C_STAT_H)
    cv.txt(ix, 2, f"species ~{cur_d}", C_HEAD)
    cv.txt(ix, 3, f"avg     {avg_d:.1f}", C_DIM)

    # divider
    def hdiv(y):
        cv.hline(sx, y, sw, '─', C_FRAME_R)
        cv.put(sx, y, '├', C_FRAME_R)
        cv.put(sx + sw - 1, y, '┤', C_FRAME_R)

    hdiv(4)
    cv.txt(ix, 5, "diversity", C_DIM)
    cv.txt(ix, 6, _sparkline(sim.div_history, iw), C_FRAME_L)

    hdiv(7)
    cv.txt(ix, 8, "lineages", C_DIM)

    clusters  = _cluster_species(sim.spawner.walkers)
    bar_max   = max((cnt for _, cnt in clusters), default=1)
    bar_w     = iw - 4   # leave 3 chars for count + 1 gap
    bar_y     = 9
    max_bars  = TOTAL_H - bar_y - 5  # leave room for divider + born + dead

    for rgb, count in clusters[:max_bars]:
        filled = max(1, int(count / bar_max * bar_w))
        for bx in range(bar_w):
            ch = '█' if bx < filled else '░'
            cv.put(ix + bx, bar_y, ch, fc=rgb)
        cv.txt(ix + bar_w + 1, bar_y, f"{count:3d}", C_DIM)
        bar_y += 1

    hdiv(TOTAL_H - 4)
    cv.txt(ix, TOTAL_H - 3, f"born {sim.spawner.total_spawned}", C_DIM)
    cv.txt(ix, TOTAL_H - 2, f"dead {sim.spawner.total_deaths}", C_DIM)

    return cv


# ── output ────────────────────────────────────────────────────────────────────
def write_capture(sim, out_dir, seed):
    cv    = render_frame(sim)
    fname = f"speciation-t{sim.tick:04d}.ans"
    header = (
        f"# title: Chromatic Schism — tick {sim.tick:05d}\n"
        f"# session: color-speciation-timeline\n"
        f"# cols: {TOTAL_W}\n"
        f"# rows: {TOTAL_H}\n"
        f"# fontsize: 12\n"
        f"# date: {datetime.now().strftime('%Y-%m-%d')}\n"
        f"# seed: {seed}\n"
        f"# tick: {sim.tick}\n"
        f"# script: scripts/speciation_capture.py\n"
        f"# params: initial_species={INITIAL_SPECIES}, "
        f"walkers_per_species={WALKERS_PER_SPECIES}, "
        f"breed_threshold={BREED_THRESHOLD}\n"
        f"# description: Two-panel: territory + walkers (left) + "
        f"species bars and diversity sparkline (right).\n"
    )
    path = out_dir / fname
    path.write_text(header + "\n" + cv.to_ansi(), encoding='utf-8')
    print(f"  wrote {path}  ({path.stat().st_size:,} bytes)")
    return fname


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed',    type=int, default=SEED)
    parser.add_argument('--out-dir', default='docs/assets/captures')
    args = parser.parse_args()

    out_dir = ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    sim = Simulation(seed=args.seed)
    print(f"Color Speciation Capture — seed={args.seed}")
    print(f"  {INITIAL_SPECIES} species × {WALKERS_PER_SPECIES} = "
          f"{INITIAL_SPECIES * WALKERS_PER_SPECIES} initial walkers")
    print(f"  breed_threshold={BREED_THRESHOLD}, breed_radius={BREED_RADIUS}")
    print(f"  checkpoints: {CHECKPOINTS}")
    print()

    for target in CHECKPOINTS:
        if sim.tick < target:
            sim.run_to(target)
        write_capture(sim, out_dir, args.seed)

    print("\nDone.")


if __name__ == '__main__':
    main()
