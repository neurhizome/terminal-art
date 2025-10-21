#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
walker_clouds_v2.py — Optimized memetic field simulation (terminal ANSI)
- Sparse dirty-cell rendering
- Vigor-weighted background color blending (no fade-to-black)
- Vector-ish diffusion at territory boundaries
- Bias-driven random walks with lineage "DNA"
"""

import argparse
import random
import shutil
import sys
import time
import math
from typing import List, Tuple, Set, Optional

# Direction bitmasks
N, NE, E, SE, S, SW, W, NW = 1, 2, 4, 8, 16, 32, 64, 128
DIRS = (N, NE, E, SE, S, SW, W, NW)
OPP = {N: S, S: N, E: W, W: E, NE: SW, SW: NE, NW: SE, SE: NW}
VEC = {
    N:  (0, -1),
    NE: (1, -1),
    E:  (1, 0),
    SE: (1, 1),
    S:  (0, 1),
    SW: (-1, 1),
    W:  (-1, 0),
    NW: (-1, -1),
}

# Unicode tile sets for non-braille styles
TILES = {
    "light": {
        0: " ", N: "│", S: "│", E: "─", W: "─", N | S: "│", E | W: "─",
        N | E: "└", E | S: "┌", S | W: "┐", W | N: "┘",
        N | E | S: "├", E | S | W: "┬", S | W | N: "┤", W | N | E: "┴", N | E | S | W: "┼",
    },
    "heavy": {
        0: " ", N: "┃", S: "┃", E: "━", W: "━", N | S: "┃", E | W: "━",
        N | E: "┗", E | S: "┏", S | W: "┓", W | N: "┛",
        N | E | S: "┣", E | S | W: "┳", S | W | N: "┫", W | N | E: "┻", N | E | S | W: "╋",
    },
    "double": {
        0: " ", N: "║", S: "║", E: "═", W: "═", N | S: "║", E | W: "═",
        N | E: "╚", E | S: "╔", S | W: "╗", W | N: "╝",
        N | E | S: "╠", E | S | W: "╦", S | W | N: "╣", W | N | E: "╩", N | E | S | W: "╬",
    },
}

def clamp(v: float, lo: float, hi: float) -> float:
    return lo if v < lo else hi if v > hi else v

def rgb_fg(r: float, g: float, b: float) -> str:
    return f"\x1b[38;2;{int(r)};{int(g)};{int(b)}m"

def rgb_bg(r: float, g: float, b: float) -> str:
    return f"\x1b[48;2;{int(r)};{int(g)};{int(b)}m"

RESET = "\x1b[0m"


class ChannelStepper:
    """Optimized color stepper - precompute path on retarget"""
    __slots__ = ("cur", "steps", "path", "idx")

    def __init__(self, cur: int, steps: int):
        self.cur = int(clamp(cur, 0, 255))
        self.steps = max(1, steps)
        self.path: List[int] = []
        self.idx = 0
        self.retarget(random.randint(0, 255))

    def retarget(self, tgt: int):
        tgt = int(clamp(tgt, 0, 255))
        d = tgt - self.cur
        sgn = 1 if d >= 0 else -1
        ad = abs(d)
        q, r = divmod(ad, self.steps)

        # Precompute the path (Bresenham-like error distribution)
        self.path = []
        err = 0
        for i in range(self.steps):
            inc = q
            err += r
            if err >= self.steps and r != 0:
                err -= self.steps
                inc += 1
            self.path.append(self.cur + sgn * inc * (i + 1))

        if self.path:
            self.path[-1] = tgt  # Ensure we hit target exactly
        self.idx = 0

    def step(self) -> int:
        if self.idx >= len(self.path):
            self.retarget(random.randint(0, 255))
        self.cur = int(self.path[self.idx])
        self.idx += 1
        return self.cur


def norm2(vx: float, vy: float) -> Tuple[float, float]:
    n = math.hypot(vx, vy)
    if n == 0:
        return (0.0, 0.0)
    return (vx / n, vy / n)

BIAS_VECTORS = [norm2(*VEC[d]) for d in DIRS]

def dir_vec(d: int) -> Tuple[float, float]:
    dx, dy = VEC[d]
    n = math.hypot(dx, dy)
    if n == 0:
        return (0.0, 0.0)
    return (dx / n, dy / n)

def weighted_choice(opts: List[int], weights: List[float]) -> int:
    total = sum(weights)
    if total <= 0:
        return random.choice(opts)
    r = random.random() * total
    acc = 0.0
    for o, w in zip(opts, weights):
        acc += w
        if r <= acc:
            return o
    return opts[-1]


class Walker:
    _next_id = 1
    __slots__ = (
        "id", "x", "y", "heading", "depth", "age", "alive",
        "R", "G", "B", "dna_R", "dna_G", "dna_B", "dna_samples",
        "bias", "bias_strength", "spawn_scale", "vigor", "lifespan", "style"
    )

    def __init__(
        self,
        x: int,
        y: int,
        heading: int,
        depth: int,
        rgb: Tuple[int, int, int],
        grad: int,
        style: str,
        lifespan: int,
        bias: Optional[Tuple[float, float]] = None,
        bias_strength: Optional[float] = None,
        spawn_scale: float = 1.0,
        vigor: Optional[float] = None,
    ):
        self.id = Walker._next_id
        Walker._next_id += 1
        self.x, self.y, self.heading = x, y, heading
        self.depth = depth
        self.age = 0
        self.alive = True
        self.R = ChannelStepper(rgb[0], grad)
        self.G = ChannelStepper(rgb[1], grad)
        self.B = ChannelStepper(rgb[2], grad)
        self.dna_R: List[int] = []
        self.dna_G: List[int] = []
        self.dna_B: List[int] = []
        self.dna_samples = 0
        self.bias = list(random.choice(BIAS_VECTORS)) if bias is None else list(bias)
        self.bias_strength = random.uniform(0.1, 0.6) if bias_strength is None else float(bias_strength)
        self.spawn_scale = float(spawn_scale)
        self.vigor = random.uniform(0.85, 1.15) if vigor is None else float(vigor)
        self.lifespan = lifespan
        self.style = style

    def rgb(self) -> Tuple[int, int, int]:
        return (self.R.step(), self.G.step(), self.B.step())

    def record_dna(self, r: int, g: int, b: int) -> None:
        if self.dna_samples < 3:
            self.dna_R.append(int(r))
            self.dna_G.append(int(g))
            self.dna_B.append(int(b))
            self.dna_samples += 1

    def dna_ready(self) -> bool:
        return self.dna_samples >= 3


class World:
    def __init__(
        self,
        cols: int,
        rows: int,
        style: str,
        wrap: bool,
        grad: int,
        lifetime: int,
        smell_ttl: int,
        mix: float,
        max_walkers: int,
        diffuse_strength: float = 0.25,
        persistence: float = 0.92,
    ):
        self.cols, self.rows = cols, rows
        self.style = style
        self.wrap = wrap
        self.grad = grad
        self.lifetime = lifetime
        self.mix = clamp(mix, 0.0, 1.0)
        self.max_walkers = max_walkers
        self.diffuse_strength = diffuse_strength  # neighbor blend weight
        self.persistence = persistence            # placeholder for alternates

        # Grid data
        self.mask: List[List[int]] = [[0] * cols for _ in range(rows)]
        self.color: List[List[Tuple[int, int, int]]] = [[(220, 220, 220)] * cols for _ in range(rows)]
        self.bg_color: List[List[Tuple[float, float, float]]] = [[(0.0, 0.0, 0.0)] * cols for _ in range(rows)]
        self.bg_vigor: List[List[float]] = [[0.0] * cols for _ in range(rows)]

        # Scent tracking
        self.scent_ttl: List[List[int]] = [[0] * cols for _ in range(rows)]
        self.scent: List[List[Optional[Tuple]]] = [[None] * cols for _ in range(rows)]

        self.walkers: List[Walker] = []
        self.spawn_base = {0: (0.02, 128), 1: (0.005, 64), 2: (0.00125, 32)}
        self.spawned_steps: dict = {}

        # Glyph cache for braille
        self._glyph_cache: dict = {}

        # Dirty tracking
        self.dirty_cells: Set[Tuple[int, int]] = set()

    def clear(self) -> None:
        self.mask = [[0] * self.cols for _ in range(self.rows)]
        self.color = [[(220, 220, 220)] * self.cols for _ in range(self.rows)]
        self.bg_color = [[(0.0, 0.0, 0.0)] * self.cols for _ in range(self.rows)]
        self.bg_vigor = [[0.0] * self.cols for _ in range(self.rows)]
        self.scent_ttl = [[0] * self.cols for _ in range(self.rows)]
        self.scent = [[None] * self.cols for _ in range(self.rows)]
        self.walkers.clear()
        self.spawned_steps.clear()
        self.dirty_cells.clear()

    def spawn(
        self,
        x: Optional[int] = None,
        y: Optional[int] = None,
        depth: int = 0,
        heading: Optional[int] = None,
        rgb: Optional[Tuple[int, int, int]] = None,
        parent: Optional[Walker] = None,
    ) -> None:
        if len(self.walkers) >= self.max_walkers:
            return
        if x is None:
            x = self.cols // 2
        if y is None:
            y = self.rows // 2
        if heading is None:
            heading = random.choice(DIRS)
        if rgb is None:
            rgb = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

        if parent:
            bx, by = parent.bias
            bx += random.uniform(-0.25, 0.25)
            by += random.uniform(-0.25, 0.25)
            bx, by = norm2(bx, by)
            bstr = clamp(parent.bias_strength + random.uniform(-0.05, 0.05), 0.05, 0.85)
            scale = clamp(parent.spawn_scale * (1 + random.uniform(-0.1, 0.1)), 0.25, 3.0)
            vigor = clamp(parent.vigor * (1 + random.uniform(-0.05, 0.05)), 0.7, 1.3)
        else:
            bx, by = random.choice(BIAS_VECTORS)
            bstr = random.uniform(0.1, 0.6)
            scale = 1.0
            vigor = random.uniform(0.85, 1.15)

        w = Walker(
            x, y, heading, depth, rgb, self.grad, self.style, self.lifetime,
            bias=(bx, by), bias_strength=bstr, spawn_scale=scale, vigor=vigor
        )
        self.walkers.append(w)
        self.spawned_steps[w.id] = 0

    def glyph(self, x: int, y: int) -> str:
        mask_val = self.mask[y][x]
        if self.style == "braille":
            g = self._glyph_cache.get(mask_val)
            if g is None:
                g = chr(0x2800 + mask_val)
                self._glyph_cache[mask_val] = g
            return g
        else:
            cardinal_mask = mask_val & (N | E | S | W)
            return TILES.get(self.style, TILES["heavy"]).get(cardinal_mask, "X")

    def choose_dir(self, w: Walker) -> int:
        opts = [d for d in DIRS if d != OPP.get(w.heading, 0)]
        bx, by = w.bias
        weights = []
        for d in opts:
            dx, dy = dir_vec(d)
            dot = max(0.0, dx * bx + dy * by)
            weights.append(1.0 + w.bias_strength * dot)
        return weighted_choice(opts, weights)

    def deposit_scent(self, w: Walker, x: int, y: int, ttl: int) -> None:
        self.scent_ttl[y][x] = ttl

        dnaR = w.dna_R if w.dna_ready() else [self.color[y][x][0]] * 3
        dnaG = w.dna_G if w.dna_ready() else [self.color[y][x][1]] * 3
        dnaB = w.dna_B if w.dna_ready() else [self.color[y][x][2]] * 3

        self.scent[y][x] = (
            w.id, tuple(dnaR), tuple(dnaG), tuple(dnaB),
            tuple(w.bias), w.spawn_scale, w.vigor
        )

        avg_r = sum(dnaR) / 3.0
        avg_g = sum(dnaG) / 3.0
        avg_b = sum(dnaB) / 3.0

        old_r, old_g, old_b = self.bg_color[y][x]
        old_vigor = self.bg_vigor[y][x]

        blend = 0.7 if w.vigor > old_vigor else 0.3

        self.bg_color[y][x] = (
            old_r * (1 - blend) + avg_r * blend,
            old_g * (1 - blend) + avg_g * blend,
            old_b * (1 - blend) + avg_b * blend,
        )
        self.bg_vigor[y][x] = max(old_vigor, w.vigor * 0.95)

        self.dirty_cells.add((x, y))

    def interact(self, w: Walker, x: int, y: int) -> None:
        ttl = self.scent_ttl[y][x]
        if ttl <= 0:
            return
        info = self.scent[y][x]
        if not info:
            return

        owner, dnaR, dnaG, dnaB, bias_vec, s_scale, vigor = info
        if owner == w.id:
            return

        if random.random() < self.mix:
            if vigor > w.vigor:
                tgtR = random.choice(dnaR)
                tgtG = random.choice(dnaG)
                tgtB = random.choice(dnaB)
                w.R.retarget(int(tgtR))
                w.G.retarget(int(tgtG))
                w.B.retarget(int(tgtB))
                w.bias = list(bias_vec)
                w.spawn_scale = clamp((w.spawn_scale + s_scale) / 2, 0.2, 4.0)
            else:
                comboR = list(dnaR) + (w.dna_R if w.dna_ready() else [])
                comboG = list(dnaG) + (w.dna_G if w.dna_ready() else [])
                comboB = list(dnaB) + (w.dna_B if w.dna_ready() else [])
                tgtR = random.choice(comboR) if comboR else self.color[y][x][0]
                tgtG = random.choice(comboG) if comboG else self.color[y][x][1]
                tgtB = random.choice(comboB) if comboB else self.color[y][x][2]
                w.R.retarget(int(tgtR))
                w.G.retarget(int(tgtG))
                w.B.retarget(int(tgtB))
                bx = 0.8 * w.bias[0] + 0.2 * bias_vec[0]
                by = 0.8 * w.bias[1] + 0.2 * bias_vec[1]
                w.bias = list(norm2(bx, by))

            win_p = clamp(0.5 + 0.2 * (w.vigor - vigor), 0.05, 0.95)
            if random.random() < win_p:
                w.spawn_scale = clamp(w.spawn_scale * 1.05, 0.2, 4.0)
            else:
                w.spawn_scale = clamp(w.spawn_scale * 0.95, 0.2, 4.0)

    def diffuse_bg_optimized(self) -> None:
        if not self.dirty_cells:
            return

        affected: Set[Tuple[int, int]] = set()
        for x, y in self.dirty_cells:
            affected.add((x, y))
            for d in DIRS:
                nx = x + VEC[d][0]
                ny = y + VEC[d][1]
                if self.wrap:
                    nx %= self.cols
                    ny %= self.rows
                elif not (0 <= nx < self.cols and 0 <= ny < self.rows):
                    continue
                affected.add((nx, ny))

        new_bg = [row[:] for row in self.bg_color]
        new_vigor = [row[:] for row in self.bg_vigor]

        for x, y in affected:
            ar, ag, ab = self.bg_color[y][x]
            av = self.bg_vigor[y][x]

            total_weight = 1.0
            for d in DIRS:
                nx = x + VEC[d][0]
                ny = y + VEC[d][1]
                if self.wrap:
                    nx %= self.cols
                    ny %= self.rows
                elif not (0 <= nx < self.cols and 0 <= ny < self.rows):
                    continue

                nr, ng, nb = self.bg_color[ny][nx]
                nv = self.bg_vigor[ny][nx]

                weight = self.diffuse_strength * (nv / (av + 1e-6) if av > 0 else 1.0)

                ar += nr * weight
                ag += ng * weight
                ab += nb * weight
                total_weight += weight

            new_bg[y][x] = (ar / total_weight, ag / total_weight, ab / total_weight)

            if self.scent_ttl[y][x] > 0:
                new_vigor[y][x] = av
            else:
                new_vigor[y][x] = av * 0.98

        self.bg_color = new_bg
        self.bg_vigor = new_vigor

    def step(self, smell_ttl: int) -> None:
        newborns = []

        for w in list(self.walkers):
            if not w.alive:
                continue

            r, g, b = w.rgb()
            w.heading = self.choose_dir(w)
            dx, dy = VEC[w.heading]
            nx, ny = w.x + dx, w.y + dy

            if self.wrap:
                nx %= self.cols
                ny %= self.rows
            else:
                if nx < 0 or nx >= self.cols:
                    w.heading = OPP.get(w.heading, w.heading)
                    dx, dy = VEC[w.heading]
                    nx = max(0, min(self.cols - 1, w.x + dx))
                if ny < 0 or ny >= self.rows:
                    w.heading = OPP.get(w.heading, w.heading)
                    dx, dy = VEC[w.heading]
                    ny = max(0, min(self.rows - 1, w.y + dy))

            self.interact(w, nx, ny)

            self.mask[w.y][w.x] |= w.heading
            self.mask[ny][nx] |= OPP.get(w.heading, w.heading)
            self.color[w.y][w.x] = (r, g, b)
            self.color[ny][nx] = (r, g, b)

            self.dirty_cells.add((w.x, w.y))
            self.dirty_cells.add((nx, ny))

            self.deposit_scent(w, w.x, w.y, smell_ttl)
            self.deposit_scent(w, nx, ny, smell_ttl)

            w.x, w.y = nx, ny
            w.age += 1
            w.record_dna(r, g, b)

            prob, win = self.spawn_base.get(w.depth, (0.0, 0))
            prob *= w.spawn_scale
            sid = w.id
            self.spawned_steps[sid] = self.spawned_steps.get(sid, 0) + 1

            if self.spawned_steps[sid] <= win and len(self.walkers) + len(newborns) < self.max_walkers:
                if random.random() < prob:
                    if w.dna_ready():
                        child_rgb = (random.choice(w.dna_R), random.choice(w.dna_G), random.choice(w.dna_B))
                    else:
                        child_rgb = (r, g, b)
                    child_hd = random.choice([d for d in DIRS if d != OPP.get(w.heading, 0)])
                    newborns.append((w, w.x, w.y, child_hd, child_rgb))

            if w.age >= w.lifespan:
                w.alive = False

        self.walkers = [w for w in self.walkers if w.alive]

        for y in range(self.rows):
            row = self.scent_ttl[y]
            for x in range(self.cols):
                if row[x] > 0:
                    row[x] -= 1
                    if row[x] <= 0:
                        self.scent[y][x] = None

        self.diffuse_bg_optimized()

        for parent, x, y, hd, rgb in newborns:
            self.spawn(x=x, y=y, depth=parent.depth + 1, heading=hd, rgb=rgb, parent=parent)

        self.render_dirty()
        self.dirty_cells.clear()

    def render_dirty(self) -> None:
        if not self.dirty_cells:
            return
        out = []
        for x, y in self.dirty_cells:
            r, g, b = self.color[y][x]
            br, bg_, bb = self.bg_color[y][x]
            out.append(f"\x1b[{y+1};{x+1}H{rgb_bg(br, bg_, bb)}{rgb_fg(r, g, b)}{self.glyph(x, y)}{RESET}")
        sys.stdout.write("".join(out))
        sys.stdout.flush()

    def render_all(self) -> None:
        out = []
        for y in range(self.rows):
            for x in range(self.cols):
                r, g, b = self.color[y][x]
                br, bg_, bb = self.bg_color[y][x]
                out.append(f"\x1b[{y+1};{x+1}H{rgb_bg(br, bg_, bb)}{rgb_fg(r, g, b)}{self.glyph(x, y)}{RESET}")
        sys.stdout.write("".join(out))
        sys.stdout.flush()


def main():
    ap = argparse.ArgumentParser(description="Optimized walker clouds with memetic color fields")
    ap.add_argument("--style", default="braille", choices=list(TILES.keys()) + ["braille"])
    ap.add_argument("--wrap", action="store_true")
    ap.add_argument("--delay", type=float, default=0.03)
    ap.add_argument("--grad", type=int, default=16)
    ap.add_argument("--lifetime", type=int, default=256)
    ap.add_argument("--smell_ttl", type=int, default=60)
    ap.add_argument("--mix", type=float, default=0.30)
    ap.add_argument("--max_walkers", type=int, default=500)
    ap.add_argument(
        "--diffuse", type=float, default=0.2,
        help="Background diffusion strength (0-1)"
    )
    ap.add_argument(
        "--persistence", type=float, default=0.92,
        help="Background color persistence (0-1) [reserved]"
    )
    ap.add_argument("--seed", type=int, default=None)
    args = ap.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    cols, lines = shutil.get_terminal_size(fallback=(100, 34))
    rows = max(8, lines - 1)
    cols = max(40, cols)

    world = World(
        cols, rows, args.style, args.wrap, args.grad, args.lifetime,
        args.smell_ttl, args.mix, args.max_walkers, args.diffuse, args.persistence
    )

    for i, bv in enumerate(BIAS_VECTORS):
        bx, by = bv
        rgb = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        x = (i + 1) * cols // (len(BIAS_VECTORS) + 1)
        y = rows // 2
        w = Walker(
            x, y, heading=random.choice(DIRS), depth=0, rgb=rgb, grad=args.grad,
            style=args.style, lifespan=args.lifetime, bias=(bx, by),
            bias_strength=random.uniform(0.25, 0.7), spawn_scale=1.0,
            vigor=random.uniform(0.9, 1.1)
        )
        world.walkers.append(w)

    hide = "\x1b[?25l"
    show = "\x1b[?25h"
    clear = "\x1b[2J"
    sys.stdout.write(hide + clear)
    sys.stdout.flush()
    world.render_all()

    try:
        while True:
            world.step(args.smell_ttl)
            if args.delay > 0:
                time.sleep(args.delay)

            ncols, nlines = shutil.get_terminal_size(fallback=(cols, lines))
            if ncols != cols or nlines != lines:
                cols, lines = ncols, nlines
                rows = max(8, lines - 1)
                cols = max(40, cols)
                world = World(
                    cols, rows, args.style, args.wrap, args.grad, args.lifetime,
                    args.smell_ttl, args.mix, args.max_walkers, args.diffuse, args.persistence
                )
                for i, bv in enumerate(BIAS_VECTORS):
                    bx, by = bv
                    rgb = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
                    x = (i + 1) * cols // (len(BIAS_VECTORS) + 1)
                    y = rows // 2
                    w = Walker(
                        x, y, heading=random.choice(DIRS), depth=0, rgb=rgb,
                        grad=args.grad, style=args.style, lifespan=args.lifetime,
                        bias=(bx, by), bias_strength=random.uniform(0.25, 0.7),
                        spawn_scale=1.0, vigor=random.uniform(0.9, 1.1)
                    )
                    world.walkers.append(w)
                sys.stdout.write(clear)
                sys.stdout.flush()
                world.render_all()
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\x1b[0m" + show + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
