#!/usr/bin/env python3
# walker_connect_color16.py
#
# Connector walker with *evenly distributed* 16-step RGB gradients.
# Each channel uses an integer Bresenham-like accumulator so tiny differences
# are spaced out over the 16 moves instead of clumping from rounding.
#
# Run:
#   python3 walker_connect_color16.py
#   python3 walker_connect_color16.py --style heavy --wrap --delay 0.001
#   python3 walker_connect_color16.py --grad 24  (longer ramps)
#
import argparse, random, shutil, sys, time
from typing import List, Tuple

# bit masks: N=1, E=2, S=4, W=8
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
    "double": {
        0:  " ",
        N:  "║", S: "║", E: "═", W: "═",
        N|S: "║", E|W: "═",
        N|E: "╚", E|S: "╔", S|W: "╗", W|N: "╝",
        N|E|S: "╠", E|S|W: "╦", S|W|N: "╣", W|N|E: "╩",
        N|E|S|W: "╬",
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

def choose_color()->Tuple[int,int,int]:
    return random.randint(0,255), random.randint(0,255), random.randint(0,255)

class ChannelStepper:
    """Integer gradient stepper that reaches target in exactly 'steps' moves,
       distributing small changes evenly (Bresenham-style)."""
    def __init__(self, cur: int, steps: int):
        self.cur = int(clamp(cur,0,255))
        self.steps = max(1, steps)
        self.left = 0
        self.sgn = 1
        self.q = 0
        self.r = 0
        self.err = 0
        self.target = self.cur

    def retarget(self, tgt: int):
        tgt = int(clamp(tgt,0,255))
        d = tgt - self.cur
        self.sgn = 1 if d >= 0 else -1
        ad = abs(d)
        self.q, self.r = divmod(ad, self.steps)   # base increment and remainder
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
            # land exactly on target at the end of the span
            self.cur = self.target
        return self.cur

def main():
    ap = argparse.ArgumentParser(description="Connector walker with evenly spaced 16-step RGB gradients")
    ap.add_argument("--style", default="heavy", choices=list(TILES.keys()))
    ap.add_argument("--delay", type=float, default=0.0, help="seconds between batches")
    ap.add_argument("--steps", type=int, default=0, help="total moves (0=infinite)")
    ap.add_argument("--batch", type=int, default=600, help="moves per flush")
    ap.add_argument("--wrap", action="store_true", help="wrap at edges instead of bouncing")
    ap.add_argument("--grad", type=int, default=16, help="steps per gradient change")
    ap.add_argument("--seed", type=int, default=None)
    args = ap.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    # Terminal size
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    cols, rows = shutil.get_terminal_size(fallback=(100, 30))
    Wc, Hc = cols, rows-1 if rows>1 else rows  # keep last row for cursor
    Wc = max(10, Wc); Hc = max(5, Hc)

    grid: List[List[int]] = [[0]*Wc for _ in range(Hc)]

    hide = "\x1b[?25l"; show = "\x1b[?25h"; clear = "\x1b[2J"; reset = "\x1b[0m"

    sys.stdout.write(hide + clear)
    sys.stdout.flush()

    # Start at center
    x = Wc//2; y = Hc//2

    # Gradient state per channel
    r0,g0,b0 = choose_color()
    R = ChannelStepper(r0, args.grad)
    G = ChannelStepper(g0, args.grad)
    B = ChannelStepper(b0, args.grad)
    # seed first targets
    R.retarget(random.randint(0,255))
    G.retarget(random.randint(0,255))
    B.retarget(random.randint(0,255))

    # initial dot
    r,g,b = R.cur, G.cur, B.cur
    sys.stdout.write(f"\x1b[{y+1};{x+1}H{color_seq(r,g,b)}•{reset}")
    sys.stdout.flush()

    heading = random.choice([N,E,S,W])
    steps_done = 0

    try:
        while True:
            out = []
            for _ in range(args.batch):
                # color step (even distribution over the span)
                r, g, b = R.step(), G.step(), B.step()
                color = color_seq(r,g,b)

                # choose next direction among non-backtracking
                choices = [d for d in (N,E,S,W) if d != OPP[heading]]
                heading = random.choice(choices)
                dx, dy = VEC[heading]
                nx, ny = x+dx, y+dy

                if args.wrap:
                    if nx < 0: nx = Wc-1
                    if nx >= Wc: nx = 0
                    if ny < 0: ny = Hc-1
                    if ny >= Hc: ny = 0
                else:
                    if nx < 0 or nx >= Wc:
                        heading = OPP[heading]; dx,dy = VEC[heading]; nx = max(0, min(Wc-1, x+dx))
                    if ny < 0 or ny >= Hc:
                        heading = OPP[heading]; dx,dy = VEC[heading]; ny = max(0, min(Hc-1, y+dy))

                # connect cells
                grid[y][x] |= heading
                grid[ny][nx] |= OPP[heading]

                ch1 = TILES[args.style].get(grid[y][x], " ")
                ch2 = TILES[args.style].get(grid[ny][nx], " ")
                out.append(f"{color}\x1b[{y+1};{x+1}H{ch1}\x1b[{ny+1};{nx+1}H{ch2}{reset}")

                x, y = nx, ny

                steps_done += 1
                if args.steps and steps_done >= args.steps:
                    break

            if out:
                sys.stdout.write("".join(out))
                sys.stdout.flush()
            if args.steps and steps_done >= args.steps:
                break
            if args.delay:
                time.sleep(args.delay)

            # lightweight resize handling: if size changes, clear and restart grid
            new_cols, new_rows = shutil.get_terminal_size(fallback=(cols, rows))
            if new_cols != cols or new_rows != rows:
                cols, rows = new_cols, new_rows
                Wc, Hc = cols, rows-1 if rows>1 else rows
                Wc = max(10, Wc); Hc = max(5, Hc)
                grid = [[0]*Wc for _ in range(Hc)]
                x = min(max(0, x), Wc-1); y = min(max(0, y), Hc-1)
                sys.stdout.write(clear)
                sys.stdout.flush()

    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write(f"\x1b[{Hc+1};1H{reset}" + show)
        sys.stdout.flush()

if __name__ == "__main__":
    main()
