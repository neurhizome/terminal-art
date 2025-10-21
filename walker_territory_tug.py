
#!/usr/bin/env python3
"""
walker_territory_tug.py — Territory Tug-of-War v1
A TerminalStage simulation with slow seasonal terrain, soft ownership,
bounded population, and genome-driven movement (no pheromones yet).

Usage:
  python walker_territory_tug.py --help   # shows defaults
"""

import argparse, colorsys, math, random, time
from typing import Dict, List, Tuple, Optional

from terminal_stage import TerminalStage, Simulation, CellState

# ------------------------- Utilities -------------------------

def clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else 1.0 if x > 1.0 else x

def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t

def wrap_mod1(x: float) -> float:
    # keep in [0,1)
    return x % 1.0

def hue_diff(a: float, b: float) -> float:
    # circular distance in [0, 0.5]
    d = abs(a - b) % 1.0
    return d if d <= 0.5 else 1.0 - d

def hsv_to_rgb255(h: float, s: float, v: float) -> Tuple[int,int,int]:
    r, g, b = colorsys.hsv_to_rgb(wrap_mod1(h), clamp01(s), clamp01(v))
    return (int(r * 255), int(g * 255), int(b * 255))

# ------------------------- Genome / Walker -------------------------

DIRS = [(0,-1), (1,0), (0,1), (-1,0)]  # N, E, S, W

class Walker:
    __slots__ = ("x","y","family","color_h","heading_bias","territory_appetite",
                 "aggression","fertility","aversion_threshold")
    def __init__(self, x:int, y:int, family:int, color_h:float, heading_bias:List[float],
                 territory_appetite:float, aggression:float, fertility:float, aversion_threshold:float):
        self.x = x
        self.y = y
        self.family = family
        self.color_h = wrap_mod1(color_h)
        # normalize heading bias to sum 1
        s = sum(max(0.0,b) for b in heading_bias) or 1.0
        self.heading_bias = [max(0.0,b)/s for b in heading_bias]
        self.territory_appetite = clamp01(territory_appetite)
        self.aggression = clamp01(aggression)
        self.fertility = clamp01(fertility)
        self.aversion_threshold = clamp01(aversion_threshold)

# ------------------------- Environment -------------------------

class Environment:
    """
    Holds terrain hue field [0..1], ownership strength per family, and helpers.
    """
    def __init__(self, width:int, height:int, families:int,
                 bg_brightness:float, bg_diffuse:float, bg_drift_rate:float):
        self.w = width
        self.h = height
        self.families = families
        # Terrain hue field
        self.hue = [[random.random() for _ in range(self.w)] for _ in range(self.h)]
        self.bg_brightness = bg_brightness
        self.bg_diffuse = bg_diffuse
        self.bg_drift_rate = bg_drift_rate
        self.global_hue_offset = random.random()
        # Ownership strengths: list[f][y][x] in [0..1]
        self.own = [[[0.0 for _ in range(self.w)] for _ in range(self.h)] for _ in range(self.families)]
        # Cached top-family map (id,strength) per cell
        self.top_family = [[(-1, 0.0) for _ in range(self.w)] for _ in range(self.h)]

    def terrain_step(self, dt:float, do_diffuse:bool=True):
        # global hue rotation
        self.global_hue_offset = wrap_mod1(self.global_hue_offset + self.bg_drift_rate * dt)
        if do_diffuse and self.bg_diffuse > 0.0:
            lam = clamp01(self.bg_diffuse)
            # simple 4-neighbor blur on hue but taking wrap-around into account
            new = [[0.0 for _ in range(self.w)] for _ in range(self.h)]
            for y in range(self.h):
                ym = (y - 1) % self.h
                yp = (y + 1) % self.h
                row = self.hue[y]
                for x in range(self.w):
                    xm = (x - 1) % self.w
                    xp = (x + 1) % self.w
                    c = row[x]
                    # average neighbors with circular hue mean:
                    neigh = [row[xm], row[xp], self.hue[ym][x], self.hue[yp][x]]
                    # convert to unit circle to average
                    import math
                    cx = math.cos(2*math.pi*c)
                    sx = math.sin(2*math.pi*c)
                    nx = sum(math.cos(2*math.pi*n) for n in neigh)
                    ns = sum(math.sin(2*math.pi*n) for n in neigh)
                    avg_angle = math.atan2(sx + ns/4.0, cx + nx/4.0)/(2*math.pi)
                    new[y][x] = wrap_mod1( (1.0 - lam)*c + lam*avg_angle )
            self.hue = new

    def ownership_decay(self, own_decay:float):
        if own_decay <= 0: 
            return
        f = clamp01(1.0 - own_decay)
        for fam in range(self.families):
            grid = self.own[fam]
            for y in range(self.h):
                row = grid[y]
                for x in range(self.w):
                    v = row[x] * f
                    row[x] = 0.0 if v < 1e-5 else v

    def deposit(self, fam:int, x:int, y:int, amount:float, home_push_levels:Tuple[float,float], home_push:float):
        # If already Medium/Heavy for this family, boost deposit
        _, current = self.top_family[y][x]
        # But current is the top family's strength; we need this family's specific strength
        my = self.own[fam][y][x]
        bonus = 0.0
        if my >= home_push_levels[0]:  # medium
            bonus = home_push
            if my >= home_push_levels[1]:  # heavy gets full
                bonus = home_push * 1.5
        v = clamp01(my + amount + bonus)
        self.own[fam][y][x] = v

    def recompute_top(self):
        for y in range(self.h):
            for x in range(self.w):
                best_f, best_v = -1, 0.0
                for f in range(self.families):
                    v = self.own[f][y][x]
                    if v > best_v:
                        best_v = v
                        best_f = f
                self.top_family[y][x] = (best_f, best_v)

    def terrain_rgb(self, x:int, y:int) -> Tuple[int,int,int]:
        h = wrap_mod1(self.hue[y][x] + self.global_hue_offset)
        # s,v chosen for dimmed background
        return hsv_to_rgb255(h, 0.5, self.bg_brightness)

# ------------------------- Simulation -------------------------

class TerritoryTug(Simulation):
    def __init__(self, stage: TerminalStage, args: argparse.Namespace):
        super().__init__(stage)
        self.args = args
        self.env: Optional[Environment] = None
        self.walkers: List[Walker] = []
        self.rng = random.Random(args.seed)

        self.families = args.families
        # family hues around the circle
        self.family_hues = [wrap_mod1(self.rng.random() + i/self.families) for i in range(self.families)]
        self.family_colors_rgb = [hsv_to_rgb255(h, 0.9, 0.85) for h in self.family_hues]

        # spawn economy
        self.spawn_budget = 0.0
        self.family_momentum = [0.0 for _ in range(self.families)]  # rolling deposits

        # cached visuals
        self.OWN_LIGHT = 0.15
        self.OWN_MED = 0.40
        self.OWN_HEAVY = 0.70

    # ---------- setup & helpers ----------

    def setup(self):
        self.stage.init_grid()
        w, h = self.stage.width, self.stage.height
        self.env = Environment(
            w, h, self.families,
            bg_brightness=self.args.bg_brightness,
            bg_diffuse=self.args.bg_diffuse,
            bg_drift_rate=self.args.bg_drift_rate
        )
        # seed terrain into coherent patches by initializing blocky hue
        self._seed_terrain_blocks(self.env)

        # seed walkers
        initial = min(self.args.max_walkers//3, max(4*self.families, 40))
        for i in range(initial):
            fam = i % self.families
            x = self.rng.randrange(w)
            y = self.rng.randrange(h)
            color_h = wrap_mod1(self.family_hues[fam] + self.rng.uniform(-0.05, 0.05))
            # heading bias
            hb = [self.rng.random() for _ in range(4)]
            territory_appetite = self.args.territory_appetite
            aggression = self.args.aggression
            fertility = self.args.fertility_base * self.rng.uniform(0.8, 1.2)
            aversion = self.args.aversion_thresh
            self.walkers.append(Walker(x,y,fam,color_h,hb,territory_appetite,aggression,fertility,aversion))

        self.env.recompute_top()

    def _seed_terrain_blocks(self, env: Environment):
        # Create large coherent patches by painting coarse blocks, then diffuse a bit
        w, h = env.w, env.h
        bx = max(6, w // 16)
        by = max(4, h // 12)
        for y in range(0, h, by):
            for x in range(0, w, bx):
                hue = self.rng.random()
                for yy in range(y, min(y+by, h)):
                    row = env.hue[yy]
                    for xx in range(x, min(x+bx, w)):
                        row[xx] = wrap_mod1(hue + self.rng.uniform(-0.02, 0.02))
        for _ in range(3):
            env.terrain_step(dt=1.0, do_diffuse=True)

    # ---------- main loop ----------

    def step(self, frame: int):
        assert self.env is not None
        env = self.env
        args = self.args

        start = time.time()

        # 1) terrain slow update
        if frame % max(1, int(args.fps//6)) == 0:
            env.terrain_step(dt=1.0/ max(1,args.fps), do_diffuse=True)

        # 2) ownership decay
        env.ownership_decay(args.own_decay)

        # 3) walkers move + deposit, track momentum
        # reset momentum slowly (rolling)
        for f in range(self.families):
            self.family_momentum[f] *= 0.98

        for w in self.walkers:
            # choose a direction
            dir_idx = self._choose_direction(w, env)
            dx, dy = DIRS[dir_idx]
            w.x = (w.x + dx) % env.w
            w.y = (w.y + dy) % env.h

            # deposit ownership
            amount = args.own_gain * (1.0 + args.w_enemy * 0.0)  # aggression reserved for v1.1 combat; left neutral
            before = env.own[w.family][w.y][w.x]
            env.deposit(w.family, w.x, w.y, amount, (self.OWN_MED, self.OWN_HEAVY), args.home_push)
            after = env.own[w.family][w.y][w.x]
            self.family_momentum[w.family] += max(0.0, after - before)

        env.recompute_top()

        # 4) spawn economy & bounds
        self._population_step()

        # 5) render
        self._render_frame(frame)

        # keep real-time-ish pacing by Simulation.run()

    # ---------- decision policy ----------

    def _choose_direction(self, w: Walker, env: Environment) -> int:
        # compute utility for 4 cardinal candidates
        best_dir = 0
        utils = []
        for i,(dx,dy) in enumerate(DIRS):
            nx = (w.x + dx) % env.w
            ny = (w.y + dy) % env.h
            # color match
            cell_h = wrap_mod1(env.hue[ny][nx] + env.global_hue_offset)
            match = 1.0 - (hue_diff(w.color_h, cell_h) * 2.0)  # to [0..1]
            # frontier: prefer low own strength
            my = env.own[w.family][ny][nx]
            frontier = 1.0 - my
            # enemy control
            best_f, best_v = env.top_family[ny][nx]
            enemy = best_v if best_f != w.family else 0.0
            # heading bias
            bias = w.heading_bias[i]

            # skip extreme mismatch (aversion)
            if match < (1.0 - w.aversion_threshold):
                util = -1e3 + bias * 0.01  # near impossible, but still break ties
            else:
                util = (self.args.w_match * match +
                        self.args.w_frontier * frontier -
                        self.args.w_enemy * enemy +
                        self.args.w_bias * bias)
            utils.append(util)

        # softmax sampling with epsilon
        eps = self.args.epsilon
        if random.random() < eps:
            return random.randrange(4)

        # softmax
        m = max(utils)
        exps = [math.exp(u - m) for u in utils]
        s = sum(exps) or 1.0
        r = random.random() * s
        acc = 0.0
        for i, e in enumerate(exps):
            acc += e
            if r <= acc:
                return i
        return best_dir

    # ---------- spawn & bounds ----------

    def _population_step(self):
        args = self.args
        # adjust budget by rate; soft caps
        soft_cap = int(args.max_walkers * args.soft_cap_mult)
        pop = len(self.walkers)
        rate = args.spawn_budget_rate
        if pop > soft_cap:
            rate *= 0.5
        if pop < args.min_pop:
            rate *= 1.6
        self.spawn_budget += rate / max(1.0, args.fps)

        # spend budget on spawns
        if pop >= args.max_walkers:
            return

        # compute family shares from momentum
        total_mom = sum(self.family_momentum) + 1e-6
        shares = []
        n = self.families
        alpha = clamp01(args.family_share_alpha)
        for f in range(n):
            p = (1.0 - alpha) * (1.0/n) + alpha * (self.family_momentum[f] / total_mom)
            shares.append(p)

        # attempt multiple spawns per frame bounded by budget
        attempts = int(self.spawn_budget // args.spawn_cost)
        attempts = min(attempts, max(1, args.max_walkers//50))
        for _ in range(attempts):
            if len(self.walkers) >= args.max_walkers or self.spawn_budget < args.spawn_cost:
                break
            fam = self._choose_family(shares)
            parent = self._pick_parent(fam)
            if not parent:
                continue
            # spawn near parent
            dx, dy = random.choice(DIRS)
            x = (parent.x + dx) % self.env.w
            y = (parent.y + dy) % self.env.h
            w = self._spawn_from_parent(parent, x, y)
            self.walkers.append(w)
            self.spawn_budget -= args.spawn_cost

    def _choose_family(self, shares: List[float]) -> int:
        r = random.random()
        acc = 0.0
        for i, p in enumerate(shares):
            acc += p
            if r <= acc:
                return i
        return len(shares) - 1

    def _pick_parent(self, fam:int) -> Optional[Walker]:
        # choose random walker of that family
        cands = [w for w in self.walkers if w.family == fam]
        if not cands:
            return None
        return random.choice(cands)

    def _spawn_from_parent(self, p: Walker, x:int, y:int) -> Walker:
        # tiny mutation
        color_h = wrap_mod1(p.color_h + random.uniform(-0.02, 0.02))
        hb = [(b + random.uniform(-0.05, 0.05)) for b in p.heading_bias]
        terr = clamp01(p.territory_appetite + random.uniform(-0.05, 0.05))
        aggr = clamp01(p.aggression + random.uniform(-0.05, 0.05))
        fert = clamp01(p.fertility + random.uniform(-0.05, 0.05))
        avert = clamp01(p.aversion_threshold + random.uniform(-0.03, 0.03))
        return Walker(x, y, p.family, color_h, hb, terr, aggr, fert, avert)

    # ---------- rendering ----------

    def _render_frame(self, frame:int):
        env = self.env
        args = self.args
        w,h = env.w, env.h

        # start with background (terrain)
        for y in range(h):
            for x in range(w):
                br, bg, bb = env.terrain_rgb(x,y)
                self.stage.cells[y][x] = CellState(glyph=" ", fg=(br,bg,bb), bg=(br,bg,bb))

        # ownership overlay (light glyphs)
        for y in range(h):
            for x in range(w):
                fam, strength = env.top_family[y][x]
                if fam < 0 or strength < self.OWN_LIGHT:
                    continue
                # choose glyph by level
                if strength >= self.OWN_HEAVY:
                    glyph = "▓"
                    inten = 1.0
                elif strength >= self.OWN_MED:
                    glyph = "▒"
                    inten = 0.8
                else:
                    glyph = "·"
                    inten = 0.6
                r,g,b = self.family_colors_rgb[fam]
                # dim by intensity
                r = int(r*inten); g=int(g*inten); b=int(b*inten)
                cell = self.stage.get_cell(x,y)
                if cell:
                    cell.glyph = glyph
                    cell.fg = (r,g,b)

        # walkers overlay
        for wkr in self.walkers:
            x,y = wkr.x, wkr.y
            r,g,b = self.family_colors_rgb[wkr.family]
            # bright glyph
            cell = self.stage.get_cell(x,y)
            if cell:
                cell.glyph = "╋"
                cell.fg = (r,g,b)

        # Optionally, small HUD in top-left
        if frame % max(1,int(args.fps//2)) == 0:
            pop = len(self.walkers)
            # write a few HUD cells
            hud = f" pop={pop}/{args.max_walkers} budget={self.spawn_budget:.1f} "
            for i,ch in enumerate(hud):
                if i < w:
                    self.stage.cells[0][i].glyph = ch
                    self.stage.cells[0][i].fg = (240,240,240)

# ------------------------- CLI -------------------------

def build_parser() -> argparse.ArgumentParser:
    P = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Territory Tug-of-War v1 — walkers, seasons, soft ownership, bounded population."
    )
    P.add_argument("--fps", type=int, default=20, help="Target frames per second")
    P.add_argument("--max-frames", type=int, default=0, help="0 = run until Ctrl-C")
    P.add_argument("--families", type=int, default=6, help="Number of factions/families")
    P.add_argument("--seed", type=int, default=0, help="RNG seed")

    # Terrain / seasons
    P.add_argument("--bg-brightness", type=float, default=0.22, help="Background brightness [0..1]")
    P.add_argument("--bg-diffuse", type=float, default=0.08, help="Terrain diffusion per update [0..1]")
    P.add_argument("--bg-drift-rate", type=float, default=0.002, help="Global hue drift per second")

    # Ownership
    P.add_argument("--own-gain", type=float, default=0.08, help="Ownership gain per step")
    P.add_argument("--own-decay", type=float, default=0.005, help="Ownership decay per tick")
    P.add_argument("--home-push", type=float, default=0.05, help="Extra gain on medium/heavy home tiles")

    # Decision weights
    P.add_argument("--w-match", type=float, default=1.00, help="Weight for color match")
    P.add_argument("--w-frontier", type=float, default=0.75, help="Weight for frontier (low own)")
    P.add_argument("--w-enemy", type=float, default=0.20, help="Weight for enemy control penalty")
    P.add_argument("--w-bias", type=float, default=0.35, help="Weight for heading bias")
    P.add_argument("--epsilon", type=float, default=0.02, help="Exploration probability")

    # Population economy
    P.add_argument("--max-walkers", type=int, default=1500, help="Hard cap on walkers")
    P.add_argument("--min-pop", type=int, default=150, help="Soft floor that boosts spawn rate")
    P.add_argument("--spawn-budget-rate", type=float, default=0.8, help="Budget refill per second")
    P.add_argument("--spawn-cost", type=float, default=1.0, help="Budget cost per spawn")
    P.add_argument("--family-share-alpha", type=float, default=0.6, help="Momentum vs uniform share mixing [0..1]")
    P.add_argument("--soft-cap-mult", type=float, default=0.85, help="Soft cap relative to max-walkers")

    # Genome ranges (initialization)
    P.add_argument("--territory-appetite", type=float, default=0.7, help="How much to value flipping low-own tiles")
    P.add_argument("--aggression", type=float, default=0.2, help="(Reserved for v1.1)")
    P.add_argument("--fertility-base", type=float, default=0.3, help="Base fertility tendency")
    P.add_argument("--aversion-thresh", type=float, default=0.35, help="Avoid very mismatched tiles [0..1]")
    return P

def main():
    parser = build_parser()
    args = parser.parse_args()

    with TerminalStage() as stage:
        sim = TerritoryTug(stage, args)
        sim.run(fps=args.fps, max_frames=args.max_frames)

if __name__ == "__main__":
    main()
