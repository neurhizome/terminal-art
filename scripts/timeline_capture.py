#!/usr/bin/env python3
"""
scripts/timeline_capture.py  –  Predator/prey timeline: 6 captures at intervals.

Runs the predator_prey simulation headlessly (no terminal, no display) and
captures frames at tick [0, 500, 1000, 2000, 3000, 5000]. Each frame is an
88×28 ANSI art piece using box-drawing chars to carve out two virtual panels:

    ┌─ SIMULATION ─────────────────────────────────────┐┌─ STATS ──────────┐
    │  scent field + prey ○ + predators ●  (60×24)     ││  counts, phase,  │
    │                                                   ││  sparklines      │
    └───────────────────────────────────────────────────┘└──────────────────┘

Output:
    docs/assets/captures/predator-prey-t0000.ans
    docs/assets/captures/predator-prey-t0500.ans
    docs/assets/captures/predator-prey-t1000.ans
    docs/assets/captures/predator-prey-t2000.ans
    docs/assets/captures/predator-prey-t3000.ans
    docs/assets/captures/predator-prey-t5000.ans

Usage:
    python scripts/timeline_capture.py [--seed N] [--out-dir PATH]
"""

import argparse
import random
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.automata import Spawner, RandomWalk, GradientFollow
from src.genetics import Genome
from src.fields import DiffusionField

# ── simulation parameters ──────────────────────────────────────────────────────
SEED            = 42
CHECKPOINTS     = [0, 500, 1000, 2000, 3000, 5000]
SIM_W, SIM_H    = 58, 22          # inner simulation grid (inside left panel)
INITIAL_PREY    = 60
INITIAL_PRED    = 15
MAX_PREY        = 400
MAX_PRED        = 130
PREY_SPAWN      = 0.12
PRED_SPAWN      = 0.03
HUNT_RADIUS     = 2.0
HIST_SAMPLES    = 22              # sparkline width (chars)
HIST_INTERVAL   = 50             # ticks between history samples

# ── canvas geometry ────────────────────────────────────────────────────────────
TOTAL_W, TOTAL_H = 88, 28
SIM_PANEL_W      = 62            # left panel outer width (includes borders)
STATS_PANEL_W    = TOTAL_W - SIM_PANEL_W  # 26

# ── colour palette ─────────────────────────────────────────────────────────────
BG        = (17,  21,  28)
C_FRAME_L = (56,  182, 194)   # teal  – sim panel border
C_FRAME_R = (80,  80,  110)   # muted purple – stats border
C_HEAD    = (200, 212, 230)   # near-white
C_DIM     = (66,  78,  100)
C_PREY    = (100, 210, 100)   # green  – prey
C_PRED    = (220, 80,  80)    # red    – predator
C_SCENT   = (20,  55,  25)    # dark green – scent background
C_TICK    = (48,  58,  80)    # subtle
C_STAT_H  = (229, 192, 123)   # amber  – stat headers
C_FULL    = (97,  175, 239)   # blue   – full bars
C_EMPTY   = (40,  50,  65)    # dim    – empty bar

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
        for ry in range(y+1, y+h-1):
            for rx in range(x+1, x+w-1):
                self.bc[ry][rx] = BG

    def hrule(self, x, y, w, color=None):
        self.put(x,   y, '├', color)
        self.hline(x+1, y, w-2, '─', color)
        self.put(x+w-1, y, '┤', color)

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


# ── simulation state ──────────────────────────────────────────────────────────
class Simulation:
    def __init__(self, seed=SEED):
        random.seed(seed)
        self.seed   = seed
        self.tick   = 0
        self.kills  = 0
        self.history = []   # list of (tick, prey_n, pred_n)

        self.prey_spawner = Spawner(max_walkers=MAX_PREY,  width=SIM_W, height=SIM_H)
        self.pred_spawner = Spawner(max_walkers=MAX_PRED,  width=SIM_W, height=SIM_H)
        self.prey_scent   = DiffusionField(SIM_W, SIM_H, diffusion_rate=0.25, decay_rate=0.92)

        self.prey_walk = RandomWalk(eight_way=True)
        self.pred_walk = GradientFollow('prey_scent', attraction=True, sensitivity=1.2)

        # initial populations
        for _ in range(INITIAL_PREY):
            g = Genome(color_h=0.33, saturation=0.8, value=0.9, vigor=1.0)
            self.prey_spawner.spawn_random(genome=g, char='○')

        for _ in range(INITIAL_PRED):
            g = Genome(color_h=0.0, saturation=0.9, value=0.9, vigor=1.5)
            self.pred_spawner.spawn_random(genome=g, char='●')

    def step(self):
        self.prey_spawner.age_all()
        self.pred_spawner.age_all()

        # prey move + scent deposit
        for prey in self.prey_spawner.walkers:
            dx, dy = self.prey_walk.get_move(prey.x, prey.y)
            prey.move(dx, dy, SIM_W, SIM_H, wrap=True)
            self.prey_scent.deposit(prey.x, prey.y, 1.0)

        # predators move + hunt
        for pred in self.pred_spawner.walkers:
            if random.random() < 0.8:
                dx, dy = self.pred_walk.get_move(pred.x, pred.y, field=self.prey_scent)
            else:
                dx, dy = self.prey_walk.get_move(pred.x, pred.y)
            pred.move(dx, dy, SIM_W, SIM_H, wrap=True)

            nearby = [p for p in self.prey_spawner.walkers
                      if pred.distance_to(p) <= HUNT_RADIUS]
            if nearby:
                victim = random.choice(nearby)
                victim.die()
                pred.modify_vigor(0.3)
                self.kills += 1

            pred.modify_vigor(-0.008)

        # prey reproduce
        if not self.prey_spawner.is_full() and random.random() < PREY_SPAWN:
            if self.prey_spawner.walkers:
                parent = random.choice(self.prey_spawner.walkers)
                cg = parent.genome.mutate(rate=0.01)
                self.prey_spawner.spawn_at(
                    parent.x + random.randint(-2, 2),
                    parent.y + random.randint(-2, 2),
                    genome=cg, char='○',
                )

        # predators reproduce
        if not self.pred_spawner.is_full() and random.random() < PRED_SPAWN:
            healthy = [p for p in self.pred_spawner.walkers if p.vigor > 1.5]
            if healthy:
                parent = random.choice(healthy)
                cg = parent.genome.mutate(rate=0.01)
                self.pred_spawner.spawn_at(
                    parent.x + random.randint(-3, 3),
                    parent.y + random.randint(-3, 3),
                    genome=cg, char='●',
                )
                parent.modify_vigor(-0.5)

        self.prey_spawner.remove_dead(max_age=600, vigor_threshold=0.1)
        self.pred_spawner.remove_dead(max_age=1000, vigor_threshold=0.2)
        self.prey_scent.update()

        if self.tick % HIST_INTERVAL == 0:
            self.history.append((
                self.tick,
                len(self.prey_spawner.walkers),
                len(self.pred_spawner.walkers),
            ))
            if len(self.history) > 200:
                self.history.pop(0)

        self.tick += 1

    def run_to(self, target_tick):
        print(f"  running to tick {target_tick}...", end='', flush=True)
        while self.tick < target_tick:
            self.step()
            if self.tick % 500 == 0:
                print(f" {self.tick}", end='', flush=True)
        print()


# ── frame renderer ────────────────────────────────────────────────────────────
def _phase(prey_n, pred_n):
    ratio = prey_n / max(1, pred_n)
    if prey_n < 10:               return "prey  collapse"
    if pred_n < 3:                return "pred  collapse"
    if ratio > 8:                 return "prey  bloom   "
    if ratio < 1.5:               return "peak  predation"
    if pred_n > INITIAL_PRED * 3: return "pred  surge   "
    return "oscillating   "


def _sparkline(values, width, max_val):
    """Render a list of floats as a sparkline string of given width."""
    if not values:
        return ' ' * width
    # sample to fit width
    n = len(values)
    if n <= width:
        sampled = values + [0] * (width - n)
    else:
        step = n / width
        sampled = [values[int(i * step)] for i in range(width)]
    if max_val <= 0:
        max_val = max(sampled) or 1
    chars = []
    for v in sampled:
        idx = int(v / max_val * (len(SPARK_CHARS) - 1))
        idx = max(0, min(idx, len(SPARK_CHARS) - 1))
        chars.append(SPARK_CHARS[idx])
    return ''.join(chars)


def _bar(filled, total, width=20):
    """Render a filled/empty progress bar."""
    if total <= 0:
        n = 0
    else:
        n = int(filled / total * width)
    n = max(0, min(n, width))
    return '█' * n + '░' * (width - n)


def render_frame(sim: Simulation) -> Canvas:
    cv = Canvas(TOTAL_W, TOTAL_H)

    prey_n = len(sim.prey_spawner.walkers)
    pred_n = len(sim.pred_spawner.walkers)
    scent  = sim.prey_scent.render()

    # ── left panel: simulation ────────────────────────────────────────────────
    lw = SIM_PANEL_W
    cv.box(0, 0, lw, TOTAL_H, C_FRAME_L, 'double',
           label=f"SIMULATION  tick {sim.tick:05d}")

    # render scent field as background tint
    for sy in range(SIM_H):
        for sx in range(SIM_W):
            char, fg_c, bg_c = scent[sy][sx]
            # subtle dark-green scent wash
            intensity = bg_c[1] / 255.0
            tinted_bg = (
                int(BG[0] + intensity * (C_SCENT[0] - BG[0])),
                int(BG[1] + intensity * (C_SCENT[1] - BG[1]) * 3),
                int(BG[2] + intensity * (C_SCENT[2] - BG[2])),
            )
            cv.bc[sy + 3][sx + 1] = tinted_bg

    # render prey
    for p in sim.prey_spawner.walkers:
        if 0 <= p.x < SIM_W and 0 <= p.y < SIM_H:
            r, g, b = p.genome.to_rgb()
            cv.put(p.x + 1, p.y + 3, '○', fc=(r, g, b))

    # render predators (on top)
    for p in sim.pred_spawner.walkers:
        if 0 <= p.x < SIM_W and 0 <= p.y < SIM_H:
            r, g, b = p.genome.to_rgb()
            cv.put(p.x + 1, p.y + 3, '●', fc=(r, g, b))

    # status strip at bottom of sim panel
    prey_str = f"○ prey {prey_n:3d}"
    pred_str = f"● pred {pred_n:3d}"
    cv.txt(2,        TOTAL_H - 2, prey_str, fc=C_PREY)
    cv.txt(2 + 12,   TOTAL_H - 2, pred_str, fc=C_PRED)
    cv.txt(lw - 14,  TOTAL_H - 2, f"kills {sim.kills:4d}", fc=C_DIM)

    # ── right panel: stats ────────────────────────────────────────────────────
    rx = SIM_PANEL_W - 1   # shared left border
    rw = STATS_PANEL_W + 1
    cv.box(rx, 0, rw, TOTAL_H, C_FRAME_R, 'single', label="STATS")

    # header
    cv.txt(rx + 2, 1, "LOTKA-VOLTERRA", fc=C_HEAD)
    cv.txt(rx + 2, 2, "predator / prey", fc=C_DIM)
    cv.hrule(rx, 3, rw, color=C_FRAME_R)

    # tick and kills
    cv.txt(rx + 2, 4, f"tick   {sim.tick:6d}", fc=C_STAT_H)
    cv.txt(rx + 2, 5, f"kills  {sim.kills:6d}", fc=C_DIM)
    cv.hrule(rx, 6, rw, color=C_FRAME_R)

    # population meters
    inner_w = rw - 4
    bar_w   = inner_w - 2   # leave 2 chars margin

    cv.txt(rx + 2, 7,  f"○ prey  {prey_n:3d}/{MAX_PREY}", fc=C_PREY)
    prey_bar = _bar(prey_n, MAX_PREY, bar_w)
    for i, c in enumerate(prey_bar):
        col = C_PREY if c == '█' else C_EMPTY
        cv.put(rx + 2 + i, 8, c, fc=col)

    cv.txt(rx + 2, 9,  f"● pred  {pred_n:3d}/{MAX_PRED}", fc=C_PRED)
    pred_bar = _bar(pred_n, MAX_PRED, bar_w)
    for i, c in enumerate(pred_bar):
        col = C_PRED if c == '█' else C_EMPTY
        cv.put(rx + 2 + i, 10, c, fc=col)

    cv.hrule(rx, 11, rw, color=C_FRAME_R)

    # ratio and phase
    ratio = prey_n / max(1, pred_n)
    cv.txt(rx + 2, 12, f"ratio  {ratio:5.1f}:1", fc=C_STAT_H)
    cv.txt(rx + 2, 13, f"phase", fc=C_DIM)
    phase = _phase(prey_n, pred_n)
    cv.txt(rx + 8, 13, phase[:inner_w - 6], fc=C_HEAD)
    cv.hrule(rx, 14, rw, color=C_FRAME_R)

    # sparklines
    spark_w = inner_w
    cv.txt(rx + 2, 15, "prey history", fc=C_DIM)
    if sim.history:
        prey_hist = [h[1] for h in sim.history[-spark_w:]]
        pred_hist = [h[2] for h in sim.history[-spark_w:]]
        max_prey  = max(prey_hist + [1])
        max_pred  = max(pred_hist + [1])
        spark_prey = _sparkline(prey_hist, spark_w, max_prey)
        spark_pred = _sparkline(pred_hist, spark_w, max_pred)
        for i, c in enumerate(spark_prey[:spark_w]):
            cv.put(rx + 2 + i, 16, c, fc=C_PREY)
        cv.txt(rx + 2, 17, "pred history", fc=C_DIM)
        for i, c in enumerate(spark_pred[:spark_w]):
            cv.put(rx + 2 + i, 18, c, fc=C_PRED)
    else:
        cv.txt(rx + 2, 16, "no history yet", fc=C_TICK)

    cv.hrule(rx, 19, rw, color=C_FRAME_R)

    # params footer
    cv.txt(rx + 2, 20, f"seed    {sim.seed}", fc=C_DIM)
    cv.txt(rx + 2, 21, f"prey_0  {INITIAL_PREY}", fc=C_DIM)
    cv.txt(rx + 2, 22, f"pred_0  {INITIAL_PRED}", fc=C_DIM)
    cv.txt(rx + 2, 23, f"hunt_r  {HUNT_RADIUS}", fc=C_DIM)

    # timestamp
    ts = datetime.now().strftime('%H:%M')
    cv.txt(rx + 2, TOTAL_H - 2, ts, fc=C_TICK)

    return cv


# ── .ans writer ────────────────────────────────────────────────────────────────
HEADER_TPL = """\
# title: Predator/Prey — tick {tick:05d}
# session: predator-prey-timeline
# cols: {cols}
# rows: {rows}
# fontsize: 12
# date: {date}
# seed: {seed}
# tick: {tick}
# script: scripts/timeline_capture.py
# params: initial_prey={ip}, initial_pred={ipd}, hunt_radius={hr}, seed={seed}
# description: Two-panel capture: simulation view (left) + population stats and sparklines (right).
"""

def save_frame(cv: Canvas, tick: int, seed: int, out_dir: Path):
    ansi   = cv.to_ansi()
    fname  = f"predator-prey-t{tick:04d}.ans"
    path   = out_dir / fname
    header = HEADER_TPL.format(
        tick=tick, cols=TOTAL_W, rows=TOTAL_H,
        date=datetime.now().strftime('%Y-%m-%d'),
        seed=seed, ip=INITIAL_PREY, ipd=INITIAL_PRED, hr=HUNT_RADIUS,
    )
    path.write_text(header + "\n" + ansi, encoding='utf-8')
    sz = path.stat().st_size
    print(f"  ✓ {fname}  ({sz:,} bytes)")
    return fname


# ── main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Predator/prey timeline captures")
    parser.add_argument('--seed',    type=int, default=SEED)
    parser.add_argument('--out-dir', default=str(ROOT / "docs" / "assets" / "captures"))
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\npredator/prey timeline  seed={args.seed}")
    print(f"checkpoints: {CHECKPOINTS}\n")

    sim   = Simulation(seed=args.seed)
    files = []
    prev  = 0

    for target in CHECKPOINTS:
        if target > prev:
            sim.run_to(target)
        cv   = render_frame(sim)
        fname = save_frame(cv, sim.tick, args.seed, out_dir)
        files.append(fname)
        prev = target

    print(f"\ndone — {len(files)} captures in {out_dir}")
    for f in files:
        print(f"  {f}")


if __name__ == '__main__':
    main()
