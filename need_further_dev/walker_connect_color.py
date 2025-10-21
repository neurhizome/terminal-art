#!/usr/bin/env python3
# walker_connect_color.py
#
# Fast connector-walker with a rolling 16-step RGB gradient.
# Starts at center with a random color. Picks a new random target color,
# computes per-channel deltas = (target - current)/16, and on each move
# adds that delta so the printed segments sweep a smooth gradient. When
# 16 steps are done, it chooses a fresh target and repeats. No deps.
#
# Run:
#   python3 walker_connect_color.py
#   python3 walker_connect_color.py --style heavy --wrap --delay 0.001
#   python3 walker_connect_color.py --steps 200000 --batch 1000
#
# Ctrl-C to stop.
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

def choose_target()->Tuple[int,int,int]:
    return random.randint(0,255), random.randint(0,255), random.randint(0,255)

def main():
    ap = argparse.ArgumentParser(description="Connector walker with 16-step RGB gradients")
    ap.add_argument("--style", default="heavy", choices=list(TILES.keys()))
    ap.add_argument("--delay", type=float, default=0.0, help="seconds between batches")
    ap.add_argument("--steps", type=int, default=0, help="limit total steps (0=infinite)")
    ap.add_argument("--batch", type=int, default=600, help="steps per screen flush")
    ap.add_argument("--wrap", action="store_true", help="wrap at edges instead of bouncing")
    ap.add_argument("--grad", type=int, default=16, help="steps per gradient segment")
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

    # Grid of masks
    grid: List[List[int]] = [[0]*Wc for _ in range(Hc)]

    # ANSI helpers
    hide = "\x1b[?25l"; show = "\x1b[?25h"; clear = "\x1b[2J"; home = "\x1b[H"; reset = "\x1b[0m"

    sys.stdout.write(hide + clear)
    sys.stdout.flush()

    # Start at center as a colored dot
    x = Wc//2; y = Hc//2

    # Gradient state
    cur_r, cur_g, cur_b = choose_target()
    tgt_r, tgt_g, tgt_b = choose_target()
    grad_n = max(1, args.grad)
    dr = (tgt_r - cur_r) / grad_n
    dg = (tgt_g - cur_g) / grad_n
    db = (tgt_b - cur_b) / grad_n
    left = grad_n

    # draw initial dot
    r,g,b = int(cur_r), int(cur_g), int(cur_b)
    sys.stdout.write(f"\x1b[{y+1};{x+1}H{color_seq(r,g,b)}•{reset}")
    sys.stdout.flush()

    # Initial heading 25% each
    heading = random.choice([N,E,S,W])

    steps_done = 0
    try:
        while True:
            out = []
            for _ in range(args.batch):
                # step the gradient
                if left <= 0:
                    cur_r, cur_g, cur_b = float(round(cur_r)), float(round(cur_g)), float(round(cur_b))
                    tgt_r, tgt_g, tgt_b = choose_target()
                    dr = (tgt_r - cur_r) / grad_n
                    dg = (tgt_g - cur_g) / grad_n
                    db = (tgt_b - cur_b) / grad_n
                    left = grad_n
                cur_r += dr; cur_g += dg; cur_b += db
                left -= 1
                r,g,b = int(clamp(round(cur_r),0,255)), int(clamp(round(cur_g),0,255)), int(clamp(round(cur_b),0,255))
                color = color_seq(r,g,b)

                # Choose next direction among non-backtracking
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
                        heading = OPP[heading]; dx,dy = VEC[heading]; nx = clamp(x+dx, 0, Wc-1)
                    if ny < 0 or ny >= Hc:
                        heading = OPP[heading]; dx,dy = VEC[heading]; ny = clamp(y+dy, 0, Hc-1)

                # connect cells
                grid[y][x] |= heading
                grid[ny][nx] |= OPP[heading]

                ch1 = TILES[args.style].get(grid[y][x], " ")
                ch2 = TILES[args.style].get(grid[ny][nx], " ")
                # one color sequence for the pair, then reset
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
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write(f"\x1b[{Hc+1};1H" + show)
        sys.stdout.flush()

if __name__ == "__main__":
    main()
