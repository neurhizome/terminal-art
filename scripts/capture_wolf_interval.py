#!/usr/bin/env python3
"""
scripts/capture_wolf_interval.py — Headless capture for Session 005

Generates 4 .ans files for docs/_posts/2026-02-21-session-005-wolf-interval.md

    wolf-interval-t0000.ans   tick 0    – full chromatic wheel
    wolf-interval-t0500.ans   tick 500  – EqualTemperament snap + restart
    wolf-interval-t1200.ans   tick 1200 – wolf shadow forms
    wolf-interval-t3000.ans   tick 3000 – two tuning schools visible

Layout: 88 × 28, two panels
    left  (63 cols): walkers coloured by hue on dark background,
                     resonance scent field as dim glow
    right (25 cols): hue histogram (12 semitone bins), drift stats,
                     wolf gap highlight
"""

import colorsys
import math
import random
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.automata import Walker, Spawner, RandomWalk, FifthSeek
from src.genetics import Genome
from src.genetics.genome import circular_distance
from src.fields import DiffusionField
from src.events import EqualTemperament

# ── constants ─────────────────────────────────────────────────────────────────

SEED             = 17
CHECKPOINTS      = [0, 500, 1200, 3000]
N_WALKERS        = 200
TUNE_RATE        = 0.0008
ET_TICK          = 500
FIFTH_TOLERANCE  = 0.035
SPATIAL_RADIUS   = 10.0
PYTHAGOREAN_FIFTH = math.log2(1.5)

TOTAL_W, TOTAL_H = 88, 28
SIM_W  = 61        # inner simulation width  (left panel 63 – 2 borders)
SIM_H  = 26        # inner simulation height (28 – 2 borders)
STATS_W = 25       # right panel outer width
SIM_PANEL_W = TOTAL_W - STATS_W    # 63

NOTE_NAMES = ['C', 'C♯', 'D', 'D♯', 'E', 'F', 'F♯', 'G', 'G♯', 'A', 'A♯', 'B']

# ── colour helpers ─────────────────────────────────────────────────────────────

BG         = (12,  16,  24)
C_FRAME_L  = (120, 180, 255)
C_FRAME_R  = (70,  70,  100)
C_HEAD     = (200, 212, 230)
C_DIM      = (60,  70,  90)
C_WOLF     = (220,  60,  60)
C_STAT_H   = (229, 192, 123)
C_GREEN    = ( 80, 200, 120)

SPARK_CHARS = ' ▁▂▃▄▅▆▇█'


def _hue_rgb(h, s=0.85, v=0.92):
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return int(r * 255), int(g * 255), int(b * 255)


def _fg(r, g, b): return f"\x1b[38;2;{r};{g};{b}m"
def _bg(r, g, b): return f"\x1b[48;2;{r};{g};{b}m"
RST = "\x1b[0m"


# ── Canvas (identical helper to speciation_capture) ───────────────────────────

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


# ── simulation helpers ────────────────────────────────────────────────────────

def find_fifth_partner(walker, walkers):
    target_h = (walker.genome.color_h + PYTHAGOREAN_FIFTH) % 1.0
    best, best_sdist = None, float('inf')
    for other in walkers:
        if other is walker:
            continue
        sdist = walker.distance_to(other)
        if sdist > SPATIAL_RADIUS:
            continue
        hdist = circular_distance(other.genome.color_h, target_h)
        if hdist < FIFTH_TOLERANCE and sdist < best_sdist:
            best, best_sdist = other, sdist
    return best


def mean_hue(walkers):
    if not walkers:
        return 0.0
    from src.genetics.genome import circular_mean
    return circular_mean([w.genome.color_h for w in walkers])


def hue_bins(walkers, n=12):
    bins = [0] * n
    for w in walkers:
        bins[int(w.genome.color_h * n) % n] += 1
    return bins


def wolf_bin(bins):
    return min(range(len(bins)), key=lambda i: bins[i])


# ── simulation ────────────────────────────────────────────────────────────────

class WolfSimulation:
    def __init__(self, seed=SEED):
        random.seed(seed)
        self.tick       = 0
        self.et_fired   = False
        self.start_hue  = None
        self.fifth_seek = FifthSeek()
        self.rand_walk  = RandomWalk(eight_way=True)

        self.spawner   = Spawner(max_walkers=N_WALKERS, width=SIM_W, height=SIM_H)
        self.resonance = DiffusionField(SIM_W, SIM_H,
                                        diffusion_rate=0.15, decay_rate=0.93)

        for i in range(N_WALKERS):
            h = (i / N_WALKERS + random.gauss(0, 0.02)) % 1.0
            genome = Genome(
                color_h=h,
                vigor=random.uniform(0.8, 1.2),
                saturation=0.85,
                value=0.9,
            )
            self.spawner.spawn_random(genome=genome)

        self.start_hue = mean_hue(self.spawner.walkers)

    def step(self):
        # Fire EqualTemperament once
        if not self.et_fired and self.tick == ET_TICK:
            for walker in self.spawner.walkers:
                k = round(walker.genome.color_h * 12) % 12
                walker.genome.color_h = k / 12.0
            self.et_fired = True

        for walker in self.spawner.walkers:
            partner = find_fifth_partner(walker, self.spawner.walkers)
            if partner is not None:
                walker.genome.tune_toward(partner.genome, rate=TUNE_RATE)
                mid_x = (walker.x + partner.x) // 2
                mid_y = (walker.y + partner.y) // 2
                self.resonance.deposit(mid_x % SIM_W, mid_y % SIM_H, 1.5)
                dx, dy = self.fifth_seek.get_move(
                    walker.x, walker.y,
                    target_x=partner.x, target_y=partner.y
                )
            else:
                dx, dy = self.rand_walk.get_move(walker.x, walker.y)
            walker.move(dx, dy, SIM_W, SIM_H, wrap=True)

        self.spawner.age_all()
        self.spawner.remove_dead(max_age=800, vigor_threshold=0.05)
        while not self.spawner.is_full() and len(self.spawner.walkers) >= 2:
            p1, p2 = random.sample(self.spawner.walkers, 2)
            self.spawner.spawn_from_parents(p1, p2, mutation_rate=0.02)

        self.resonance.update()
        self.tick += 1

    def run_to(self, target):
        print(f"  running to tick {target}...", end='', flush=True)
        while self.tick < target:
            self.step()
            if self.tick % 500 == 0:
                print(f" {self.tick}", end='', flush=True)
        print()


# ── frame renderer ────────────────────────────────────────────────────────────

def render_frame(sim):
    cv = Canvas(TOTAL_W, TOTAL_H)

    cur_hue   = mean_hue(sim.spawner.walkers)
    drift     = (cur_hue - sim.start_hue) % 1.0
    if drift > 0.5:
        drift -= 1.0
    drift_c   = drift * 1200   # cents

    bins      = hue_bins(sim.spawner.walkers)
    wb        = wolf_bin(bins)
    expected  = len(sim.spawner.walkers) / 12
    wolf_frac = bins[wb] / expected if expected > 0 else 1.0
    wolf_gap  = wolf_frac < 0.35

    # ── left panel: simulation ────────────────────────────────────────────────
    label = f"WOLF INTERVAL  tick {sim.tick:05d}"
    cv.box(0, 0, SIM_PANEL_W, TOTAL_H, C_FRAME_L, style='double', label=label)

    # Resonance glow: dim the background where resonance is high
    res_max = max(max(row) for row in sim.resonance.grid) or 1.0
    for ry in range(SIM_H):
        for rx in range(SIM_W):
            val = sim.resonance.grid[ry][rx]
            if val > 0.05:
                norm = val / res_max
                intensity = int(norm * 30)
                cv.bc[ry + 1][rx + 1] = (intensity, intensity + 5, intensity + 15)

    # Walkers
    for w in sim.spawner.walkers:
        if 0 <= w.x < SIM_W and 0 <= w.y < SIM_H:
            h = w.genome.color_h
            bin_i = int(h * 12) % 12
            is_wolf = (bin_i == wb) and wolf_gap
            r, g, b = _hue_rgb(h, s=0.6 if is_wolf else 0.9, v=0.5 if is_wolf else 0.92)
            char = '▓' if is_wolf else '●'
            cv.put(w.x + 1, w.y + 1, char, fc=(r, g, b))

    # ── right panel: hue histogram ────────────────────────────────────────────
    sx = SIM_PANEL_W
    sw = STATS_W
    ix = sx + 1
    iw = sw - 2

    cv.box(sx, 0, sw, TOTAL_H, C_FRAME_R, style='single', label=' PITCH ')

    # Stats header
    pop = len(sim.spawner.walkers)
    cv.txt(ix, 1, f"pop  {pop:3d}", C_STAT_H)
    drift_col = C_WOLF if abs(drift_c) > 5 else C_GREEN
    cv.txt(ix, 2, f"drift {drift_c:+6.1f}¢", drift_col)
    cv.txt(ix, 3, f"ET   {'fired' if sim.et_fired else 'pending'}", C_DIM)

    def hdiv(y, label=None):
        cv.hline(sx, y, sw, '─', C_FRAME_R)
        cv.put(sx,      y, '├', C_FRAME_R)
        cv.put(sx+sw-1, y, '┤', C_FRAME_R)
        if label:
            cv.txt(sx + 2, y, f" {label} ", C_DIM)

    hdiv(4, "hue bins")

    # Hue histogram: 12 bins, one row each (y = 5..16)
    bin_max = max(bins) or 1
    bar_w   = iw - 5    # leave 2 chars for note name + 1 gap + 2 for count
    for i, count in enumerate(bins):
        y      = 5 + i
        is_w   = (i == wb) and wolf_gap
        note   = NOTE_NAMES[i]
        hue    = i / 12
        col    = C_WOLF if is_w else _hue_rgb(hue, s=0.7, v=0.8)
        filled = max(0, int(count / bin_max * bar_w))

        # Note name
        cv.txt(ix, y, f"{note:<3}", col)
        # Bar
        for bx in range(bar_w):
            ch = '█' if bx < filled else '░'
            shade = tuple(int(c * (0.4 if bx >= filled else 1.0)) for c in col)
            cv.put(ix + 3 + bx, y, ch, fc=shade)
        # Count
        cv.txt(ix + 3 + bar_w, y, f"{count:2d}", C_DIM)

    hdiv(17)

    # Wolf alert
    if wolf_gap:
        cv.txt(ix, 18, "WOLF GAP", C_WOLF)
        cv.txt(ix, 19, f"bin {wb:2d} {NOTE_NAMES[wb]:<3}", C_WOLF)
        cv.txt(ix, 20, f"{wolf_frac:.0%} expected", C_DIM)
    else:
        cv.txt(ix, 18, "gap: none yet", C_DIM)
        cv.txt(ix, 19, f"min bin {wb:2d}", C_DIM)
        cv.txt(ix, 20, f"{wolf_frac:.0%} expected", C_DIM)

    hdiv(21)
    cv.txt(ix, 22, f"Pythagorean fifth", C_DIM)
    cv.txt(ix, 23, f"  {math.log2(1.5):.5f}", C_HEAD)
    cv.txt(ix, 24, f"ET seventh  7/12", C_DIM)
    cv.txt(ix, 25, f"  {7/12:.5f}", C_DIM)

    return cv


# ── output ────────────────────────────────────────────────────────────────────

def write_capture(sim, out_dir):
    cv    = render_frame(sim)
    fname = f"wolf-interval-t{sim.tick:04d}.ans"
    header = (
        f"# title: Wolf Interval — tick {sim.tick:05d}\n"
        f"# session: 005-wolf-interval\n"
        f"# cols: {TOTAL_W}\n"
        f"# rows: {TOTAL_H}\n"
        f"# date: {datetime.now().strftime('%Y-%m-%d')}\n"
        f"# seed: {SEED}\n"
        f"# tick: {sim.tick}\n"
        f"# script: scripts/capture_wolf_interval.py\n"
        f"# params: walkers={N_WALKERS}, tune_rate={TUNE_RATE}, "
        f"et_tick={ET_TICK}\n"
        f"# description: Two-panel: walkers coloured by pitch (left) + "
        f"hue histogram showing comma drift and wolf gap (right).\n"
    )
    path = out_dir / fname
    path.write_text(header + "\n" + cv.to_ansi(), encoding='utf-8')
    print(f"  wrote {path}  ({path.stat().st_size:,} bytes)")


def main():
    out_dir = ROOT / "docs" / "assets" / "captures"
    out_dir.mkdir(parents=True, exist_ok=True)

    sim = WolfSimulation(seed=SEED)
    print(f"Wolf Interval Capture — seed={SEED}")
    print(f"  {N_WALKERS} walkers, tune_rate={TUNE_RATE}, ET at tick {ET_TICK}")
    print(f"  checkpoints: {CHECKPOINTS}")
    print()

    for target in CHECKPOINTS:
        if sim.tick < target:
            sim.run_to(target)
        write_capture(sim, out_dir)

    print("\nDone.")


if __name__ == '__main__':
    main()
