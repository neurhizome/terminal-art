#!/usr/bin/env python3
# walker_bloom.py
#
# Branching connector-walker with "color DNA" and very slow bloom.
# - Starts at the center with a random RGB.
# - Each move uses a Bresenham-like per-channel stepper toward a random color.
# - After its first 3 moves, a walker records those 3 RGBs as immutable "DNA".
# - Spawning (bifurcation):
#   depth 0: for the next 128 steps, 2.0% chance per step to spawn a child.
#   depth 1: for the next  64 steps, 0.5% chance per step to spawn a child.
#   depth 2: for the next  32 steps, 0.125% chance per step to spawn a child.
#   depth>=3: no further spawning.
# - A child’s initial RGB is formed by independently picking R,G,B from the
#   parent’s DNA channel triplets (each with equal probability among the 3).
# - Every walker lives exactly 256 steps and then stops.
#
# Tuned for in-place terminal animation; stdlib-only.
#
# Run:
#   python3 walker_bloom.py                  # slow default
#   python3 walker_bloom.py --wrap           # wrap at edges
#   python3 walker_bloom.py --delay 0.03     # tweak pacing
#   python3 walker_bloom.py --max_branches 600 --style heavy
#
import argparse, random, shutil, sys, time
from typing import List, Tuple

# ---- directions & tiles ----
N,E,S,W = 1,2,4,8
OPP = {N:S, S:N, E:W, W:E}
VEC = {N:(0,-1), S:(0,1), E:(1,0), W:(-1,0)}

TILES = {
    "light": {
        0:  " ",
        N:  "│", S: "│", E: "─", W: "─",
        N|S: "│", E|W: "─",
        N|E: "└", E|S: "┌", S|W: "┐", W|N: "┘",
        N|E|S: "├", E|S|W: "┬", S|W|N: "┤", W|N|E: "┴",
        N|E|S|W: "┼",
    },
    "heavy": {
        0:  " ",
        N:  "┃", S: "┃", E: "━", W: "━",
        N|S: "┃", E|W: "━",
        N|E: "┗", E|S: "┏", S|W: "┓", W|N: "┛",
        N|E|S: "┣", E|S|W: "┳", S|W|N: "┫", W|N|E: "┻",
        N|E|S|W: "╋",
    },
    "rounded": {
        0:  " ",
        N:  "│", S: "│", E: "─", W: "─",
        N|S: "│", E|W: "─",
        N|E: "╰", E|S: "╭", S|W: "╮", W|N: "╯",
        N|E|S: "├", E|S|W: "┬", S|W|N: "┤", W|N|E: "┴",
        N|E|S|W: "┼",
    },
}

def clamp(v, lo, hi): 
    return lo if v<lo else hi if v>hi else v

def color_seq(r:int,g:int,b:int)->str:
    return f"\x1b[38;2;{r};{g};{b}m"

# ---- color steppers ----
class ChannelStepper:
    """Evenly distributes integer channel changes across 'steps' moves."""
    def __init__(self, cur: int, steps: int):
        self.cur = int(clamp(cur,0,255))
        self.steps = max(1, steps)
        self.left = 0
        self.sgn = 1
        self.q = 0
        self.r = 0
        self.err = 0
        self.target = self.cur
        self.retarget(random.randint(0,255))

    def retarget(self, tgt: int):
        tgt = int(clamp(tgt,0,255))
        d = tgt - self.cur
        self.sgn = 1 if d >= 0 else -1
        ad = abs(d)
        self.q, self.r = divmod(ad, self.steps)
        self.err = 0
        self.left = self.steps
        self.target = tgt

    def step(self) -> int:
        if self.left <= 0:
            self.retarget(random.randint(0,255))
        inc = self.q
        self.err += self.r
        if self.err >= self.steps and self.r != 0:
            self.err -= self.steps
            inc += 1
        self.cur = int(clamp(self.cur + self.sgn*inc, 0, 255))
        self.left -= 1
        if self.left == 0:
            self.cur = self.target
        return self.cur

# ---- walker ----
class Walker:
    __slots__ = ("x","y","heading","depth","age","alive",
                 "R","G","B","dna_R","dna_G","dna_B","dna_samples",
                 "spawn_rate","spawn_window","spawned_steps","style")

    def __init__(self, x:int, y:int, heading:int, depth:int, rgb:Tuple[int,int,int],
                 grad:int, style:str):
        self.x, self.y, self.heading = x, y, heading
        self.depth = depth
        self.age = 0
        self.alive = True
        self.R = ChannelStepper(rgb[0], grad)
        self.G = ChannelStepper(rgb[1], grad)
        self.B = ChannelStepper(rgb[2], grad)
        # DNA sampling for first 3 steps
        self.dna_R: List[int] = []
        self.dna_G: List[int] = []
        self.dna_B: List[int] = []
        self.dna_samples = 0
        # spawning schedule based on depth
        if depth == 0:
            self.spawn_rate, self.spawn_window = 0.02, 128
        elif depth == 1:
            self.spawn_rate, self.spawn_window = 0.01, 64
        elif depth == 2:
            self.spawn_rate, self.spawn_window = 0.005, 32
        else:
            self.spawn_rate, self.spawn_window = 0.0, 0
        self.spawned_steps = 0
        self.style = style

    def rgb(self)->Tuple[int,int,int]:
        return (self.R.step(), self.G.step(), self.B.step())

    def record_dna(self, r:int,g:int,b:int):
        if self.dna_samples < 3:
            self.dna_R.append(r); self.dna_G.append(g); self.dna_B.append(b)
            self.dna_samples += 1

    def dna_ready(self)->bool:
        return self.dna_samples >= 3

# ---- main ----
def main():
    ap = argparse.ArgumentParser(description="Branching color-DNA walker bloom")
    ap.add_argument("--style", default="heavy", choices=list(TILES.keys()))
    ap.add_argument("--delay", type=float, default=0.06, help="seconds between frames (slow = larger)")
    ap.add_argument("--wrap", action="store_true", help="wrap at edges instead of bouncing")
    ap.add_argument("--grad", type=int, default=16, help="steps per color glide")
    ap.add_argument("--lifetime", type=int, default=256, help="steps a walker lives")
    ap.add_argument("--max_branches", type=int, default=400, help="cap total walkers")
    ap.add_argument("--seed", type=int, default=None)
    args = ap.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    cols, rows = shutil.get_terminal_size(fallback=(100, 30))
    Wc, Hc = cols, rows-1 if rows>1 else rows
    Wc = max(20, Wc); Hc = max(8, Hc)

    grid: List[List[int]] = [[0]*Wc for _ in range(Hc)]
    hide = "\x1b[?25l"; show = "\x1b[?25h"; clear = "\x1b[2J"; reset = "\x1b[0m"
    sys.stdout.write(hide + clear); sys.stdout.flush()

    # seed root walker
    cx, cy = Wc//2, Hc//2
    start_rgb = (random.randint(0,255), random.randint(0,255), random.randint(0,255))
    root = Walker(cx, cy, random.choice([N,E,S,W]), 0, start_rgb, args.grad, args.style)
    walkers: List[Walker] = [root]

    def draw_cell(x:int,y:int, style:str)->str:
        ch = TILES[style].get(grid[y][x], " ")
        return f"\x1b[{y+1};{x+1}H{ch}"

    try:
        while True:
            out = []
            # step each walker once
            new_walkers: List[Walker] = []
            for w in walkers:
                if not w.alive:
                    continue
                r,g,b = w.rgb()
                color = color_seq(r,g,b)

                # choose next direction among non-backtracking
                choices = [d for d in (N,E,S,W) if d != OPP[w.heading]]
                w.heading = random.choice(choices)
                dx, dy = VEC[w.heading]
                nx, ny = w.x + dx, w.y + dy

                # boundaries
                if args.wrap:
                    if nx < 0: nx = Wc-1
                    if nx >= Wc: nx = 0
                    if ny < 0: ny = Hc-1
                    if ny >= Hc: ny = 0
                else:
                    if nx < 0 or nx >= Wc:
                        w.heading = OPP[w.heading]; dx,dy = VEC[w.heading]
                        nx = max(0, min(Wc-1, w.x+dx))
                    if ny < 0 or ny >= Hc:
                        w.heading = OPP[w.heading]; dx,dy = VEC[w.heading]
                        ny = max(0, min(Hc-1, w.y+dy))

                # connect tiles
                grid[w.y][w.x] |= w.heading
                grid[ny][nx] |= OPP[w.heading]

                # draw the two tiles in current color
                out.append(f"{color}{draw_cell(w.x,w.y,w.style)}{draw_cell(nx,ny,w.style)}{reset}")

                # DNA sampling for first 3 steps
                w.record_dna(r,g,b)

                # advance
                w.x, w.y = nx, ny
                w.age += 1

                # spawning window begins after DNA ready (after 3 steps)
                if w.dna_ready():
                    w.spawned_steps += 1
                    if w.spawned_steps <= w.spawn_window and len(walkers)+len(new_walkers) < args.max_branches:
                        if random.random() < w.spawn_rate:
                            # pick child heading different from reverse to branch
                            branch_choices = [d for d in (N,E,S,W) if d != OPP[w.heading]]
                            child_heading = random.choice(branch_choices)
                            # child initial RGB from parent's DNA triplets
                            child_rgb = (
                                random.choice(w.dna_R),
                                random.choice(w.dna_G),
                                random.choice(w.dna_B),
                            )
                            child = Walker(w.x, w.y, child_heading, w.depth+1, child_rgb, args.grad, w.style)
                            new_walkers.append(child)

                # lifetime
                if w.age >= args.lifetime:
                    w.alive = False

            if new_walkers:
                walkers.extend(new_walkers)

            if out:
                sys.stdout.write("".join(out)); sys.stdout.flush()

            # slow pacing
            if args.delay > 0:
                time.sleep(args.delay)

            # stop if everyone died and no new sprouts
            if not any(w.alive for w in walkers):
                break

            # handle resize gently
            new_cols, new_rows = shutil.get_terminal_size(fallback=(cols, rows))
            if new_cols != cols or new_rows != rows:
                cols, rows = new_cols, new_rows
                Wc, Hc = cols, rows-1 if rows>1 else rows
                Wc = max(20, Wc); Hc = max(8, Hc)
                grid = [[0]*Wc for _ in range(Hc)]
                # clamp or wrap walkers into new bounds
                for w in walkers:
                    if args.wrap:
                        w.x %= Wc; w.y %= Hc
                    else:
                        w.x = max(0, min(Wc-1, w.x))
                        w.y = max(0, min(Hc-1, w.y))
                sys.stdout.write(clear); sys.stdout.flush()

    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write(f"\x1b[{Hc+1};1H\x1b[0m" + "\x1b[?25h")
        sys.stdout.flush()

if __name__ == "__main__":
    main()
