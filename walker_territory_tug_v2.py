
#!/usr/bin/env python3
"""
walker_territory_tug_v2.py — Optimized Territory Tug-of-War (memetic color)

Key ideas:
- Chunked ownership grid for fewer computations.
- Emergent color: chunks remember recent visitors' hues.
- Walkers carry COLOR as primary genome trait (not tied to family).
- Families are spawn networks only.
- Children inherit parent color with drift -> natural gradients.
- Terminal rendering uses cached terrain and minimal diff from TerminalStage.

Run:
  python walker_territory_tug_v2.py --help
"""

import argparse
import colorsys
import math
import random
from typing import Dict, List, Tuple, Optional, Set

from terminal_stage import TerminalStage, Simulation, CellState

# -------------------- Utilities --------------------

def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))

def wrap_mod1(x: float) -> float:
    return x % 1.0

def hue_diff(a: float, b: float) -> float:
    d = abs(a - b) % 1.0
    return d if d <= 0.5 else 1.0 - d

def hsv_to_rgb255(h: float, s: float, v: float) -> Tuple[int, int, int]:
    r, g, b = colorsys.hsv_to_rgb(wrap_mod1(h), clamp01(s), clamp01(v))
    return (int(r * 255), int(g * 255), int(b * 255))

def circular_mean_hue(hues: List[float], weights: Optional[List[float]] = None) -> float:
    """Compute circular mean of hues in [0,1) with optional weights."""
    if not hues:
        return 0.0
    if weights is None:
        weights = [1.0] * len(hues)
    cos_sum = sum(w * math.cos(2 * math.pi * h) for h, w in zip(hues, weights))
    sin_sum = sum(w * math.sin(2 * math.pi * h) for h, w in zip(hues, weights))
    if cos_sum == 0 and sin_sum == 0:
        return 0.0
    return (math.atan2(sin_sum, cos_sum) / (2 * math.pi)) % 1.0

# -------------------- Genome / Walker --------------------

DIRS = [(0,-1), (1,0), (0,1), (-1,0)]  # N, E, S, W

class Walker:
    __slots__ = ("x","y","family","color_h","heading_bias","territory_appetite",
                 "fertility","aversion_threshold","age","last_dir")
    def __init__(self, x:int, y:int, family:int, color_h:float, heading_bias:List[float],
                 territory_appetite:float, fertility:float, aversion_threshold:float):
        self.x = x
        self.y = y
        self.family = family  # just spawn network; color is independent
        self.color_h = wrap_mod1(color_h)  # primary identity
        s = sum(max(0.0, b) for b in heading_bias) or 1.0
        self.heading_bias = [max(0.0, b) / s for b in heading_bias]
        self.territory_appetite = clamp01(territory_appetite)
        self.fertility = clamp01(fertility)
        self.aversion_threshold = clamp01(aversion_threshold)
        self.age = 0
        self.last_dir = 0

# -------------------- Chunked Ownership Grid --------------------

class ChunkedOwnership:
    """
    Ownership tracking at lower resolution than the display grid.
    Each chunk tracks: family strengths, top family, and recent visitor color memory.
    """
    def __init__(self, display_w:int, display_h:int, chunk_size:int, families:int):
        self.chunk_size = max(1, chunk_size)
        self.cw = max(1, (display_w + self.chunk_size - 1) // self.chunk_size)
        self.ch = max(1, (display_h + self.chunk_size - 1) // self.chunk_size)
        self.families = families

        # Per-chunk family strengths
        self.strength: List[List[List[float]]] = [
            [[0.0 for _ in range(self.cw)] for _ in range(self.ch)]
            for _ in range(families)
        ]

        # Cached top (family, strength) per chunk
        self.top: List[List[Tuple[int, float]]] = [
            [(-1, 0.0) for _ in range(self.cw)] for _ in range(self.ch)
        ]

        # Color memory per chunk: list of (hue, weight)
        self.color_memory: List[List[List[Tuple[float, float]]]] = [
            [[] for _ in range(self.cw)] for _ in range(self.ch)
        ]

        # Dirty chunks to recompute
        self.dirty_chunks: Set[Tuple[int, int]] = set()

    def world_to_chunk(self, x:int, y:int) -> Tuple[int, int]:
        return (x // self.chunk_size, y // self.chunk_size)

    def deposit(self, fam:int, x:int, y:int, amount:float, color_h:float):
        """Deposit ownership and record walker color in chunk memory."""
        cx, cy = self.world_to_chunk(x, y)
        if not (0 <= cx < self.cw and 0 <= cy < self.ch):
            return

        old = self.strength[fam][cy][cx]
        new = clamp01(old + amount)
        if new != old:
            self.strength[fam][cy][cx] = new
            self.dirty_chunks.add((cx, cy))

        mem = self.color_memory[cy][cx]
        mem.append((color_h, amount))
        if len(mem) > 12:  # recent history only
            mem.pop(0)

    def decay(self, rate:float):
        """Decay ownership and fade color memory weights."""
        if rate <= 0:
            return
        factor = max(0.0, 1.0 - rate)

        for fam in range(self.families):
            grid = self.strength[fam]
            for cy in range(self.ch):
                row = grid[cy]
                for cx in range(self.cw):
                    old = row[cx]
                    if old > 1e-5:
                        new = old * factor
                        if new < 1e-5:
                            new = 0.0
                        if new != old:
                            row[cx] = new
                            self.dirty_chunks.add((cx, cy))

        # fade color memory
        for cy in range(self.ch):
            for cx in range(self.cw):
                mem = self.color_memory[cy][cx]
                if mem:
                    new_mem = [(h, w * factor) for (h, w) in mem if w * factor > 0.01]
                    self.color_memory[cy][cx] = new_mem

    def recompute_dirty(self):
        for cx, cy in list(self.dirty_chunks):
            best_f, best_v = -1, 0.0
            for f in range(self.families):
                v = self.strength[f][cy][cx]
                if v > best_v:
                    best_v = v
                    best_f = f
            self.top[cy][cx] = (best_f, best_v)
        self.dirty_chunks.clear()

    def get_chunk_color(self, cx:int, cy:int) -> float:
        """Emergent color from visitor memory; default 0.0 if empty."""
        mem = self.color_memory[cy][cx]
        if not mem:
            return 0.0
        hues = [h for (h, _w) in mem]
        weights = [w for (_h, w) in mem]
        return circular_mean_hue(hues, weights)

    def get_ownership(self, x:int, y:int) -> Tuple[int, float]:
        """Top family and strength at world position (via chunk)."""
        cx, cy = self.world_to_chunk(x, y)
        if not (0 <= cx < self.cw and 0 <= cy < self.ch):
            return (-1, 0.0)
        return self.top[cy][cx]

# -------------------- Environment --------------------

class Environment:
    def __init__(self, width:int, height:int, families:int, chunk_size:int,
                 bg_brightness:float, bg_drift_rate:float):
        self.w = width
        self.h = height
        self.families = families

        # Global terrain hue (uniform) for simplicity & speed
        self.terrain_hue = random.random()
        self.bg_brightness = bg_brightness
        self.bg_drift_rate = bg_drift_rate

        self.ownership = ChunkedOwnership(width, height, chunk_size, families)

    def terrain_step(self, dt:float):
        self.terrain_hue = wrap_mod1(self.terrain_hue + self.bg_drift_rate * dt)

    def terrain_rgb(self, x:int, y:int) -> Tuple[int, int, int]:
        return hsv_to_rgb255(self.terrain_hue, 0.4, self.bg_brightness)

# -------------------- Simulation --------------------

class TerritoryTugV2(Simulation):
    def __init__(self, stage: TerminalStage, args: argparse.Namespace):
        super().__init__(stage)
        self.args = args
        self.env: Optional[Environment] = None
        self.walkers: List[Walker] = []
        self.rng = random.Random(args.seed)

        self.families = args.families
        # Initial seed hues per family; walkers will drift from these
        self.family_seed_hues = [
            wrap_mod1(i / self.families + self.rng.uniform(-0.1, 0.1))
            for i in range(self.families)
        ]

        # Spawn economy
        self.spawn_budget = 0.0

        # Render cache (terrain)
        self.last_terrain_hue = 0.0

        # Ownership display thresholds
        self.OWN_LIGHT = 0.10
        self.OWN_MED = 0.30
        self.OWN_HEAVY = 0.60

    def setup(self):
        self.stage.init_grid()
        w, h = self.stage.width, self.stage.height

        self.env = Environment(
            w, h, self.families,
            chunk_size=self.args.chunk_size,
            bg_brightness=self.args.bg_brightness,
            bg_drift_rate=self.args.bg_drift_rate
        )

        # Seed walkers (clustered by family, but color will drift)
        initial = min(self.args.max_walkers // 3, max(4 * self.families, 40))
        for i in range(initial):
            fam = i % self.families
            x = self.rng.randrange(w)
            y = self.rng.randrange(h)
            color_h = wrap_mod1(self.family_seed_hues[fam] + self.rng.uniform(-0.08, 0.08))
            hb = [self.rng.random() for _ in range(4)]
            self.walkers.append(Walker(
                x, y, fam, color_h, hb,
                self.args.territory_appetite,
                self.args.fertility_base * self.rng.uniform(0.8, 1.2),
                self.args.aversion_thresh
            ))

        self.last_terrain_hue = self.env.terrain_hue

    # ---------- Decision policy ----------

    def _choose_direction(self, w: Walker, env: Environment) -> int:
        args = self.args
        weights: List[float] = []

        for i, (dx, dy) in enumerate(DIRS):
            nx = (w.x + dx) % env.w
            ny = (w.y + dy) % env.h
            cx, cy = env.ownership.world_to_chunk(nx, ny)

            # match to chunk's emergent color
            if 0 <= cx < env.ownership.cw and 0 <= cy < env.ownership.ch:
                chunk_color = env.ownership.get_chunk_color(cx, cy)
                match = 1.0 - hue_diff(w.color_h, chunk_color)
            else:
                match = 0.5

            # frontier & enemy
            fam, strength = env.ownership.get_ownership(nx, ny)
            frontier = 1.0 - strength
            enemy = strength if (fam >= 0 and fam != w.family) else 0.0

            bias = w.heading_bias[i]

            score = (args.w_match * match +
                     args.w_frontier * frontier * w.territory_appetite +
                     args.w_bias * bias -
                     args.w_enemy * enemy)

            weights.append(max(0.01, score))

        # epsilon-greedy
        if self.rng.random() < args.epsilon:
            return self.rng.randrange(4)

        total = sum(weights)
        r = self.rng.random() * total
        acc = 0.0
        for i, wt in enumerate(weights):
            acc += wt
            if r <= acc:
                return i
        return 0

    def _spawn_from_parent(self, p: Walker, x:int, y:int) -> Walker:
        # memetic color inheritance + gaussian drift
        color_h = wrap_mod1(p.color_h + self.rng.gauss(0, 0.03))
        hb = [max(0.0, b + self.rng.uniform(-0.08, 0.08)) for b in p.heading_bias]
        terr = clamp01(p.territory_appetite + self.rng.uniform(-0.05, 0.05))
        fert = clamp01(p.fertility + self.rng.uniform(-0.03, 0.03))
        avert = clamp01(p.aversion_threshold + self.rng.uniform(-0.03, 0.03))
        return Walker(x, y, p.family, color_h, hb, terr, fert, avert)

    # ---------- Rendering ----------

    def _render_frame_fast(self, frame:int):
        env = self.env
        args = self.args
        w, h = env.w, env.h

        # If terrain hue changed enough, repaint base
        terrain_changed = abs(env.terrain_hue - self.last_terrain_hue) > 0.01
        if terrain_changed or frame == 0:
            self.last_terrain_hue = env.terrain_hue
            base_rgb = env.terrain_rgb(0, 0)
            for y in range(h):
                for x in range(w):
                    self.stage.cells[y][x] = CellState(glyph=" ", fg=base_rgb, bg=base_rgb)

        # Ownership overlay (chunks) with emergent chunk color
        for cy in range(env.ownership.ch):
            for cx in range(env.ownership.cw):
                fam, strength = env.ownership.top[cy][cx]
                if fam < 0 or strength < self.OWN_LIGHT:
                    continue

                chunk_hue = env.ownership.get_chunk_color(cx, cy)

                if strength >= self.OWN_HEAVY:
                    glyph = "▓"
                    sat, val = 0.7, 0.6
                elif strength >= self.OWN_MED:
                    glyph = "▒"
                    sat, val = 0.6, 0.5
                else:
                    glyph = "·"
                    sat, val = 0.5, 0.4

                r, g, b = hsv_to_rgb255(chunk_hue, sat, val)

                x0 = cx * env.ownership.chunk_size
                y0 = cy * env.ownership.chunk_size
                x1 = min(x0 + env.ownership.chunk_size, w)
                y1 = min(y0 + env.ownership.chunk_size, h)

                for yy in range(y0, y1):
                    for xx in range(x0, x1):
                        cell = self.stage.get_cell(xx, yy)
                        if cell:
                            cell.glyph = glyph
                            cell.fg = (r, g, b)

        # Walkers with their own colors
        for wkr in self.walkers:
            cell = self.stage.get_cell(wkr.x, wkr.y)
            if cell:
                r, g, b = hsv_to_rgb255(wkr.color_h, 0.9, 0.9)
                cell.glyph = "●"
                cell.fg = (r, g, b)

        # HUD
        if frame % max(1, int(args.fps // 2)) == 0:
            pop = len(self.walkers)
            hud = f" pop={pop}/{args.max_walkers} "
            for i, ch in enumerate(hud):
                if i < w:
                    self.stage.cells[0][i].glyph = ch
                    self.stage.cells[0][i].fg = (240, 240, 240)

    # ---------- Step ----------

    def step(self, frame:int):
        env = self.env
        args = self.args

        # terrain drift
        if frame % max(1, int(args.fps // 6)) == 0:
            env.terrain_step(dt=1.0 / max(1, args.fps))

        # ownership decay
        env.ownership.decay(args.own_decay)

        # walkers move & deposit
        for w in self.walkers:
            w.age += 1
            dir_idx = self._choose_direction(w, env)
            dx, dy = DIRS[dir_idx]
            w.x = (w.x + dx) % env.w
            w.y = (w.y + dy) % env.h
            w.last_dir = dir_idx

            # deposit ownership + color
            env.ownership.deposit(w.family, w.x, w.y, args.own_gain, w.color_h)

        # recompute dirty chunk tops
        env.ownership.recompute_dirty()

        # lifespan cull
        max_age = 800
        if len(self.walkers) > 0:
            self.walkers = [w for w in self.walkers if w.age < max_age]

        # spawn economy
        self._update_spawn_budget()

        # render
        self._render_frame_fast(frame)

    def _update_spawn_budget(self):
        args = self.args
        env = self.env
        pop = len(self.walkers)

        # budget accumulation with soft caps
        rate = args.spawn_budget_rate
        if pop > args.max_walkers * 0.85:
            rate *= 0.5
        if pop < args.min_pop:
            rate *= 1.6
        self.spawn_budget += rate / max(1.0, args.fps)

        if pop >= args.max_walkers or self.spawn_budget < args.spawn_cost:
            return

        attempts = min(int(self.spawn_budget // args.spawn_cost), max(1, args.max_walkers // 50))
        for _ in range(attempts):
            if len(self.walkers) >= args.max_walkers or self.spawn_budget < args.spawn_cost:
                break
            if not self.walkers:
                break
            parent = self.rng.choice(self.walkers)
            dx, dy = self.rng.choice(DIRS)
            x = (parent.x + dx) % env.w
            y = (parent.y + dy) % env.h
            child = self._spawn_from_parent(parent, x, y)
            self.walkers.append(child)
            self.spawn_budget -= args.spawn_cost

# -------------------- CLI --------------------

def build_parser() -> argparse.ArgumentParser:
    P = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Territory Tug v2 — Optimized with memetic color gradients"
    )
    P.add_argument("--fps", type=int, default=30, help="Target FPS")
    P.add_argument("--max-frames", type=int, default=0, help="0 = infinite")
    P.add_argument("--families", type=int, default=6, help="Spawn network count")
    P.add_argument("--seed", type=int, default=0, help="RNG seed")

    # Performance / ownership
    P.add_argument("--chunk-size", type=int, default=4, help="Ownership chunk size (larger = faster)")

    # Terrain
    P.add_argument("--bg-brightness", type=float, default=0.18, help="Background value for terrain")
    P.add_argument("--bg-drift-rate", type=float, default=0.001, help="Global terrain hue drift per second")

    # Ownership
    P.add_argument("--own-gain", type=float, default=0.12, help="Ownership gain per step")
    P.add_argument("--own-decay", type=float, default=0.008, help="Ownership decay per tick")

    # Decision weights
    P.add_argument("--w-match", type=float, default=1.2, help="Weight for color match")
    P.add_argument("--w-frontier", type=float, default=0.8, help="Weight for frontier (low own)")
    P.add_argument("--w-enemy", type=float, default=0.3, help="Penalty for enemy control")
    P.add_argument("--w-bias", type=float, default=0.4, help="Weight for heading bias")
    P.add_argument("--epsilon", type=float, default=0.02, help="Exploration probability")

    # Population
    P.add_argument("--max-walkers", type=int, default=1200, help="Hard cap on walkers")
    P.add_argument("--min-pop", type=int, default=120, help="Soft floor that boosts spawn rate")
    P.add_argument("--spawn-budget-rate", type=float, default=1.0, help="Budget refill per second")
    P.add_argument("--spawn-cost", type=float, default=1.0, help="Budget cost per spawn")

    # Genome init
    P.add_argument("--territory-appetite", type=float, default=0.7, help="How much to value flipping low-own chunks")
    P.add_argument("--fertility-base", type=float, default=0.35, help="Base fertility tendency")
    P.add_argument("--aversion-thresh", type=float, default=0.35, help="Avoid very mismatched tiles [0..1]")
    return P

def main():
    parser = build_parser()
    args = parser.parse_args()
    with TerminalStage() as stage:
        sim = TerritoryTugV2(stage, args)
        sim.run(fps=args.fps, max_frames=args.max_frames)

if __name__ == "__main__":
    main()
