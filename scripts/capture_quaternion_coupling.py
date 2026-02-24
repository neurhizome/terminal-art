#!/usr/bin/env python3
"""
scripts/capture_quaternion_coupling.py — Headless capture for Session 006

Generates 4 .ans files for docs/_posts/2026-02-23-session-006-the-seam-as-comma.md

    quaternion-coupling-affinity005.ans  affinity=0.05, tick 1500  – near-commutative
    quaternion-coupling-affinity035.ans  affinity=0.35, tick 1500  – coherence window
    quaternion-coupling-affinity080.ans  affinity=0.80, tick 1500  – overcoupled
    quaternion-coupling-seam-closeup.ans affinity=0.35, tick 3000  – seam detail

Layout: 88 × 28, two panels
    left  (63 cols): territory background + walkers coloured by quaternion hue
                     walkers dim at low affinity, bright at high affinity
    right (25 cols): affinity distribution, crossing stats, coupling notes
"""

import colorsys
import math
import random
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.automata import Walker, Spawner, RandomWalk, GradientFollow
from src.genetics import QuaternionGenome
from src.fields import DiffusionField, TerritoryField

# ── constants ─────────────────────────────────────────────────────────────────

SEED = 23

# (affinity, tick, output_suffix)
CAPTURES = [
    (0.05, 1500, "affinity005"),
    (0.35, 1500, "affinity035"),
    (0.80, 1500, "affinity080"),
    (0.35, 3000, "seam-closeup"),
]

N_WALKERS    = 180
BREED_RADIUS = 6.0

TOTAL_W, TOTAL_H = 88, 28
SIM_W  = 61
SIM_H  = 26
SIM_PANEL_W = 63
STATS_W     = TOTAL_W - SIM_PANEL_W   # 25

# ── colour helpers ────────────────────────────────────────────────────────────

BG        = (12,  16,  24)
C_FRAME_L = (180, 100, 220)
C_FRAME_R = (70,  70,  100)
C_HEAD    = (200, 212, 230)
C_DIM     = (60,  70,  90)
C_STAT_H  = (229, 192, 123)
C_LEFT    = ( 80, 200, 120)   # green lineage
C_RIGHT   = (220,  80,  80)   # red lineage
C_SEAM    = (220, 180,  80)   # seam / mixed

SPARK_CHARS = ' ▁▂▃▄▅▆▇█'


def _fg(r, g, b): return f"\x1b[38;2;{r};{g};{b}m"
def _bg(r, g, b): return f"\x1b[48;2;{r};{g};{b}m"
RST = "\x1b[0m"


def _hue_rgb(h, s=0.85, v=0.92):
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return int(r * 255), int(g * 255), int(b * 255)


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

def _affinity_char(aff):
    if aff < 0.15: return '·'
    if aff < 0.35: return '○'
    if aff < 0.55: return '●'
    if aff < 0.75: return '◉'
    return '⬟'


class QuaternionSimulation:
    def __init__(self, affinity, seed=SEED):
        random.seed(seed)
        self.tick     = 0
        self.affinity = affinity
        self.rand_walk = RandomWalk(eight_way=True)

        self.spawner   = Spawner(max_walkers=N_WALKERS, width=SIM_W, height=SIM_H)
        self.scent     = DiffusionField(SIM_W, SIM_H,
                                        diffusion_rate=0.18, decay_rate=0.94)
        self.territory = TerritoryField(SIM_W, SIM_H, chunk_size=6)

        mid = SIM_W // 2

        # Left lineage: green-cyan  hue≈0.33
        for _ in range(N_WALKERS // 2):
            h   = (0.33 + random.gauss(0, 0.03)) % 1.0
            aff = max(0.0, min(0.99, affinity + random.gauss(0, 0.05)))
            g   = QuaternionGenome.from_hue(h, affinity=aff,
                                            vigor=random.uniform(0.8, 1.2))
            x = random.randint(0, mid - 1)
            y = random.randint(0, SIM_H - 1)
            self.spawner.spawn_at(x, y, genome=g)

        # Right lineage: red-orange  hue≈0.0
        for _ in range(N_WALKERS // 2):
            h   = (0.0 + random.gauss(0, 0.03)) % 1.0
            aff = max(0.0, min(0.99, affinity + random.gauss(0, 0.05)))
            g   = QuaternionGenome.from_hue(h, affinity=aff,
                                            vigor=random.uniform(0.8, 1.2))
            x = random.randint(mid, SIM_W - 1)
            y = random.randint(0, SIM_H - 1)
            self.spawner.spawn_at(x, y, genome=g)

    def _seam_stats(self):
        mid = SIM_W // 2
        left_in_right = right_in_left = 0
        for w in self.spawner.walkers:
            h = w.genome.color_h
            is_warm = (h < 0.20 or h > 0.85)
            if w.x < mid and is_warm:
                right_in_left += 1
            elif w.x >= mid and not is_warm:
                left_in_right += 1
        n = max(1, len(self.spawner.walkers))
        return left_in_right / n, right_in_left / n

    def step(self):
        for walker in self.spawner.walkers:
            g = walker.genome
            self.scent.deposit(walker.x, walker.y, g.vigor * 0.5)
            self.territory.claim(walker)

            if random.random() < 0.65:
                dx, dy = GradientFollow('scent', attraction=True).get_move(
                    walker.x, walker.y, field=self.scent
                )
            else:
                dx, dy = self.rand_walk.get_move(walker.x, walker.y)
            walker.move(dx, dy, SIM_W, SIM_H, wrap=True)

        if (not self.spawner.is_full()
                and self.spawner.walkers
                and random.random() < 0.06):
            ini = random.choice(self.spawner.walkers)
            nbrs = self.spawner.find_neighbors(ini, BREED_RADIUS)
            comp = [p for p in nbrs if ini.genome.can_breed_with(p.genome)]
            if comp:
                partner = random.choice(comp)
                child_g = ini.genome.reproduce_with(partner.genome, mutation_rate=0.025)
                cx = (2 * ini.x + partner.x) // 3
                cy = (2 * ini.y + partner.y) // 3
                child = Walker(cx % SIM_W, cy % SIM_H, genome=child_g)
                self.spawner.add(child)

        self.spawner.age_all()
        self.spawner.remove_dead(max_age=700, vigor_threshold=0.05)

        # Repopulate — handles the case where population collapses to <2
        attempts = 0
        while (not self.spawner.is_full()
               and self.spawner.walkers
               and attempts < 20):
            attempts += 1
            if len(self.spawner.walkers) >= 2:
                p1, p2 = random.sample(self.spawner.walkers, 2)
                if p1.genome.can_breed_with(p2.genome):
                    self.spawner.spawn_from_parents(p1, p2, mutation_rate=0.03)
                    continue
            # Fallback: mutate a surviving walker
            src = random.choice(self.spawner.walkers)
            new_g = src.genome.mutate(0.04)
            self.spawner.spawn_at(
                (src.x + random.randint(-4, 4)) % SIM_W,
                (src.y + random.randint(-4, 4)) % SIM_H,
                genome=new_g
            )

        self.scent.update()
        self.territory.update()
        active_ids = {id(w) for w in self.spawner.walkers}
        self.territory.prune_genomes(active_ids)
        self.tick += 1

    def run_to(self, target):
        print(f"  aff={self.affinity:.2f}  running to tick {target}...",
              end='', flush=True)
        while self.tick < target:
            self.step()
            if self.tick % 500 == 0:
                print(f" {self.tick}", end='', flush=True)
        print()


# ── frame renderer ────────────────────────────────────────────────────────────

def render_frame(sim, label_suffix=""):
    cv = Canvas(TOTAL_W, TOTAL_H)

    label = f"QUATERNION COUPLING  aff={sim.affinity:.2f}  tick {sim.tick:05d}"
    if label_suffix:
        label = f"QC seam close-up  aff={sim.affinity:.2f}  tick {sim.tick:05d}"

    cv.box(0, 0, SIM_PANEL_W, TOTAL_H, C_FRAME_L, style='double', label=label)

    # Territory background (dim)
    ter = sim.territory.render()
    for ry in range(SIM_H):
        for rx in range(SIM_W):
            _, _, bg = ter[ry][rx]
            if bg and bg != (0, 0, 0):
                cv.bc[ry + 1][rx + 1] = (
                    int(bg[0] * 0.35),
                    int(bg[1] * 0.35),
                    int(bg[2] * 0.35),
                )

    # Seam line marker
    mid = SIM_W // 2
    for ry in range(SIM_H):
        current_bc = cv.bc[ry + 1][mid]
        cv.bc[ry + 1][mid] = (
            min(255, current_bc[0] + 20),
            min(255, current_bc[1] + 20),
            min(255, current_bc[2] + 30),
        )

    # Walkers
    for w in sim.spawner.walkers:
        if 0 <= w.x < SIM_W and 0 <= w.y < SIM_H:
            r, g, b = w.genome.to_rgb()
            aff   = w.genome.resonance_affinity
            boost = 0.55 + 0.45 * aff
            r, g, b = (min(255, int(r * boost)),
                       min(255, int(g * boost)),
                       min(255, int(b * boost)))
            char = _affinity_char(aff)
            cv.put(w.x + 1, w.y + 1, char, fc=(r, g, b))

    # ── right panel ───────────────────────────────────────────────────────────
    sx = SIM_PANEL_W
    sw = STATS_W
    ix = sx + 1
    iw = sw - 2

    cv.box(sx, 0, sw, TOTAL_H, C_FRAME_R, style='single', label=' SEAM ')

    pop = len(sim.spawner.walkers)
    avg_aff = (sum(w.genome.resonance_affinity for w in sim.spawner.walkers)
               / max(1, pop))
    lin_l, lin_r = sim._seam_stats()

    cv.txt(ix, 1, f"pop   {pop:3d}", C_STAT_H)
    cv.txt(ix, 2, f"aff   {avg_aff:.3f}", C_HEAD)

    def hdiv(y, lbl=None):
        cv.hline(sx, y, sw, '─', C_FRAME_R)
        cv.put(sx,      y, '├', C_FRAME_R)
        cv.put(sx+sw-1, y, '┤', C_FRAME_R)
        if lbl:
            cv.txt(sx + 2, y, f" {lbl} ", C_DIM)

    hdiv(3, "crossings")
    cv.txt(ix, 4, "L→R", C_LEFT)
    cv.txt(ix + 4, 4, f"{lin_l:5.1%}", C_STAT_H)
    cv.txt(ix, 5, "R→L", C_RIGHT)
    cv.txt(ix + 4, 5, f"{lin_r:5.1%}", C_STAT_H)

    hdiv(6, "affinity")
    aff_bins = [0] * 5
    for w in sim.spawner.walkers:
        aff_bins[min(4, int(w.genome.resonance_affinity * 5))] += 1
    aff_labels = ['·', '○', '●', '◉', '⬟']
    aff_max = max(aff_bins) or 1
    bar_w = iw - 4
    for i, (lbl, cnt) in enumerate(zip(aff_labels, aff_bins)):
        y      = 7 + i
        filled = max(0, int(cnt / aff_max * bar_w))
        frac   = i / 4
        col    = _hue_rgb(0.15 + frac * 0.5, v=0.5 + frac * 0.5)
        cv.txt(ix, y, lbl, col)
        for bx in range(bar_w):
            ch = '█' if bx < filled else '░'
            shade = tuple(int(c * (1.0 if bx < filled else 0.3)) for c in col)
            cv.put(ix + 2 + bx, y, ch, fc=shade)
        cv.txt(ix + 2 + bar_w, y, f"{cnt:3d}", C_DIM)

    hdiv(12, "non-comm")

    # Show the non-commutativity note: A×B vs B×A hue values
    # Draw an indicative pair for this affinity level
    g1 = QuaternionGenome.from_hue(0.33, affinity=sim.affinity)
    g2 = QuaternionGenome.from_hue(0.00, affinity=sim.affinity)
    random.seed(SEED + 1)
    c_ab = g1.reproduce_with(g2, mutation_rate=0.0)
    random.seed(SEED + 1)
    c_ba = g2.reproduce_with(g1, mutation_rate=0.0)
    diff = abs(c_ab.color_h - c_ba.color_h)
    if diff > 0.5:
        diff = 1.0 - diff

    cv.txt(ix, 13, "A×B hue", C_DIM)
    col_ab = _hue_rgb(c_ab.color_h)
    cv.txt(ix + 8, 13, f"{c_ab.color_h:.3f}", col_ab)
    for bx in range(min(iw, 8)):
        cv.put(ix + bx, 14, '█', fc=_hue_rgb(c_ab.color_h))

    cv.txt(ix, 15, "B×A hue", C_DIM)
    col_ba = _hue_rgb(c_ba.color_h)
    cv.txt(ix + 8, 15, f"{c_ba.color_h:.3f}", col_ba)
    for bx in range(min(iw, 8)):
        cv.put(ix + bx, 16, '█', fc=_hue_rgb(c_ba.color_h))

    hdiv(17)
    diff_cents = diff * 1200
    diff_col = C_SEAM if diff > 0.05 else C_DIM
    cv.txt(ix, 18, f"Δhue {diff:.3f}", diff_col)
    cv.txt(ix, 19, f"     {diff_cents:+.0f}¢", diff_col)

    hdiv(20, "regime")
    regime = ("near-commutative" if sim.affinity < 0.15 else
              "coherence window" if sim.affinity < 0.60 else
              "overcoupled")
    regime_col = (C_DIM if sim.affinity < 0.15 else
                  C_LEFT if sim.affinity < 0.60 else
                  C_RIGHT)
    # word-wrap to iw
    words = regime.split()
    line, lines = [], []
    for w in words:
        if len(' '.join(line + [w])) <= iw:
            line.append(w)
        else:
            lines.append(' '.join(line))
            line = [w]
    if line:
        lines.append(' '.join(line))
    for li, ln in enumerate(lines[:4]):
        cv.txt(ix, 21 + li, ln, regime_col)

    return cv


# ── output ────────────────────────────────────────────────────────────────────

def write_capture(sim, out_dir, suffix):
    fname = f"quaternion-coupling-{suffix}.ans"
    label_suffix = "closeup" if "closeup" in suffix else ""
    cv = render_frame(sim, label_suffix)
    header = (
        f"# title: Quaternion Coupling — {suffix} — tick {sim.tick:05d}\n"
        f"# session: 006-the-seam-as-comma\n"
        f"# cols: {TOTAL_W}\n"
        f"# rows: {TOTAL_H}\n"
        f"# date: {datetime.now().strftime('%Y-%m-%d')}\n"
        f"# seed: {SEED}\n"
        f"# tick: {sim.tick}\n"
        f"# script: scripts/capture_quaternion_coupling.py\n"
        f"# params: affinity={sim.affinity:.2f}, walkers={N_WALKERS}\n"
        f"# description: Two-panel: territory + walkers (left) + "
        f"seam stats, affinity histogram, non-commutativity indicator (right).\n"
    )
    path = out_dir / fname
    path.write_text(header + "\n" + cv.to_ansi(), encoding='utf-8')
    print(f"  wrote {path}  ({path.stat().st_size:,} bytes)")


def main():
    out_dir = ROOT / "docs" / "assets" / "captures"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Quaternion Coupling Capture")
    print(f"  {N_WALKERS} walkers, seed={SEED}")
    print()

    # Group captures by affinity to avoid re-running simulations
    # Sort so we run lower ticks before higher (for same affinity)
    sorted_caps = sorted(CAPTURES, key=lambda c: (c[0], c[1]))

    prev_aff = None
    sim = None
    for affinity, target_tick, suffix in sorted_caps:
        if affinity != prev_aff:
            sim = QuaternionSimulation(affinity=affinity, seed=SEED)
            prev_aff = affinity
        sim.run_to(target_tick)
        write_capture(sim, out_dir, suffix)

    print("\nDone.")


if __name__ == '__main__':
    main()
