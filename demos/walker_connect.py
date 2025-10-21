#!/usr/bin/env python3
# walker_connect.py
#
# A fast terminal walker that starts as a dot at the center and grows using
# box-drawing connectors. It chooses an initial heading uniformly among N,E,S,W,
# then at each step picks uniformly among the three non-backtracking directions
# (forward/left/right). It draws only the changed cells for speed.
#
# Run:
#   python3 walker_connect.py
#   python3 walker_connect.py --style heavy --delay 0.0 --steps 200000
#   python3 walker_connect.py --style light --wrap --delay 0.002
#
# Ctrl-C to stop cleanly.
#
# Stdlib-only. UTF-8 terminal recommended.
import argparse, random, shutil, sys, time
from typing import List

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

def main():
    ap = argparse.ArgumentParser(description="Growing line walker with box connectors")
    ap.add_argument("--style", default="heavy", choices=list(TILES.keys()))
    ap.add_argument("--delay", type=float, default=0.0, help="seconds between batches")
    ap.add_argument("--steps", type=int, default=0, help="limit total steps (0=infinite)")
    ap.add_argument("--batch", type=int, default=500, help="steps per screen flush")
    ap.add_argument("--wrap", action="store_true", help="wrap at edges instead of bouncing")
    args = ap.parse_args()

    # Terminal size
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    cols, rows = shutil.get_terminal_size(fallback=(100, 30))
    # Use full canvas
    Wc, Hc = cols, rows-1 if rows>1 else rows  # keep last row for cursor
    Wc = max(10, Wc); Hc = max(5, Hc)

    # Grid of masks
    grid: List[List[int]] = [[0]*Wc for _ in range(Hc)]

    # ANSI helpers
    hide = "\x1b[?25l"
    show = "\x1b[?25h"
    clear = "\x1b[2J"
    home = "\x1b[H"

    sys.stdout.write(hide + clear)
    sys.stdout.flush()

    # Start at center as a dot
    x = Wc//2; y = Hc//2
    dot = "•"
    sys.stdout.write(f"\x1b[{y+1};{x+1}H{dot}")
    sys.stdout.flush()

    # Initial heading 25% each
    heading = random.choice([N,E,S,W])

    steps_done = 0
    try:
        while True:
            # batch multiple steps for speed
            out = []
            for _ in range(args.batch):
                # Choose next direction: among three non-backtracking dirs
                choices = [d for d in (N,E,S,W) if d != OPP[heading]]
                heading = random.choice(choices)

                dx, dy = VEC[heading]
                nx, ny = x+dx, y+dy

                # boundary handling
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

                # connect current cell to next
                grid[y][x] |= heading
                grid[ny][nx] |= OPP[heading]

                # draw the two affected cells
                ch1 = TILES[args.style].get(grid[y][x], " ")
                ch2 = TILES[args.style].get(grid[ny][nx], " ")
                out.append(f"\x1b[{y+1};{x+1}H{ch1}")
                out.append(f"\x1b[{ny+1};{nx+1}H{ch2}")

                # advance
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
        # move cursor below drawing and show it
        sys.stdout.write(f"\x1b[{Hc+1};1H" + show)
        sys.stdout.flush()

if __name__ == "__main__":
    main()
