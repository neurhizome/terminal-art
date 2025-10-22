#!/usr/bin/env python3
"""
Mobile-Optimized Directional Walker

Lightweight version optimized for:
- Mobile devices (iSH on iOS, Termux on Android)
- Constrained environments
- Single-width characters only (no display breakage!)
- Lower memory usage
- Simpler rendering

Features:
- Proper NESW connection tracking
- Probabilistic glyph selection
- Optional perturbative events
- All characters guaranteed single-width
"""
import argparse
import math
import random
import shutil
import sys
import time
from pathlib import Path
from typing import List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.glyphs import GlyphPicker, Direction, OPPOSITES

# ANSI codes
def hide_cursor(): return "\x1b[?25l"
def show_cursor(): return "\x1b[?25h"
def clear_screen(): return "\x1b[2J"
def reset_color(): return "\x1b[0m"
def goto(x, y): return f"\x1b[{y+1};{x+1}H"
def color_rgb(r, g, b): return f"\x1b[38;2;{r};{g};{b}m"

def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


class ConnectorGrid:
    """Maintains NESW connection masks for each cell."""
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.grid: List[List[int]] = [[0] * width for _ in range(height)]

    def get(self, x: int, y: int) -> int:
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y][x]
        return 0

    def add_connection(self, x: int, y: int, direction: Direction):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[y][x] |= direction


def main():
    ap = argparse.ArgumentParser(description="Mobile-optimized probabilistic walker")
    ap.add_argument("--database", default="glyph_database_optimized.json",
                   help="Glyph database JSON (use optimized version!)")
    ap.add_argument("--intensity", type=float, default=0.5,
                   help="Base intensity (0.0-1.0)")
    ap.add_argument("--style", default=None,
                   help="Style filter (arrow, connector, line, etc.)")
    ap.add_argument("--delay", type=float, default=0.0,
                   help="Seconds between batches")
    ap.add_argument("--batch", type=int, default=100,
                   help="Moves per batch (lower=smoother, higher=faster)")
    ap.add_argument("--wrap", action="store_true",
                   help="Wrap at edges")
    ap.add_argument("--no-color", action="store_true",
                   help="Disable colors (faster)")
    ap.add_argument("--simple", action="store_true",
                   help="Simple mode (no status line, even faster)")
    args = ap.parse_args()

    # Load database
    try:
        picker = GlyphPicker.from_json(args.database)
        if not args.simple:
            print(f"Loaded {len(picker)} glyphs from {args.database}")
            print("Press Ctrl+C to exit")
            time.sleep(1)
    except FileNotFoundError:
        print(f"Error: {args.database} not found!")
        print("\nBuild it with:")
        print("  python3 tools/build_optimized_db.py -o glyph_database_optimized.json")
        sys.exit(1)

    # Terminal setup
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    cols, rows = shutil.get_terminal_size(fallback=(80, 24))
    Wc = cols
    Hc = rows - (0 if args.simple else 2)  # Leave room for status if not simple

    # Initialize grid
    grid = ConnectorGrid(Wc, Hc)

    sys.stdout.write(hide_cursor() + clear_screen())
    sys.stdout.flush()

    # Walker state
    x, y = Wc // 2, Hc // 2
    heading = Direction.E

    # Color state
    r, g, b = random.randint(120, 255), random.randint(120, 255), random.randint(120, 255)

    frame = 0

    try:
        while True:
            out = []

            for _ in range(args.batch):
                # Choose next direction (no backtracking)
                opposite = OPPOSITES.get(heading, Direction.NONE)
                choices = [d for d in [Direction.N, Direction.E, Direction.S, Direction.W]
                          if d != opposite]
                heading = random.choice(choices)

                # Calculate next position
                dx, dy = 0, 0
                if heading == Direction.N:
                    dy = -1
                elif heading == Direction.S:
                    dy = 1
                elif heading == Direction.E:
                    dx = 1
                elif heading == Direction.W:
                    dx = -1

                nx, ny = x + dx, y + dy

                # Boundary handling
                if args.wrap:
                    nx = nx % Wc
                    ny = ny % Hc
                else:
                    if nx < 0 or nx >= Wc or ny < 0 or ny >= Hc:
                        # Bounce
                        heading = OPPOSITES[heading]
                        dx, dy = -dx, -dy
                        nx = clamp(x + dx, 0, Wc - 1)
                        ny = clamp(y + dy, 0, Hc - 1)

                # Update connection grid
                grid.add_connection(x, y, heading)
                grid.add_connection(nx, ny, OPPOSITES[heading])

                # Get connection masks
                cur_mask = grid.get(x, y)
                next_mask = grid.get(nx, ny)

                # Convert mask to combined Direction for picker
                cur_dir = Direction.NONE
                if cur_mask & 1: cur_dir |= Direction.N
                if cur_mask & 2: cur_dir |= Direction.E
                if cur_mask & 4: cur_dir |= Direction.S
                if cur_mask & 8: cur_dir |= Direction.W

                next_dir = Direction.NONE
                if next_mask & 1: next_dir |= Direction.N
                if next_mask & 2: next_dir |= Direction.E
                if next_mask & 4: next_dir |= Direction.S
                if next_mask & 8: next_dir |= Direction.W

                # Get glyphs using probabilistic picker
                cur_char = picker.get(
                    direction=cur_dir,
                    intensity=args.intensity,
                    style=args.style
                )
                next_char = picker.get(
                    direction=next_dir,
                    intensity=args.intensity,
                    style=args.style
                )

                # Color variation (optional)
                if not args.no_color and frame % 20 == 0:
                    r = clamp(r + random.randint(-15, 15), 100, 255)
                    g = clamp(g + random.randint(-15, 15), 100, 255)
                    b = clamp(b + random.randint(-15, 15), 100, 255)

                color = color_rgb(r, g, b) if not args.no_color else ""

                # Draw both cells
                out.append(f"{color}{goto(x, y)}{cur_char}{goto(nx, ny)}{next_char}{reset_color()}")

                x, y = nx, ny
                frame += 1

            # Flush output
            if out:
                sys.stdout.write("".join(out))

                # Show status line (if not simple mode)
                if not args.simple:
                    status = f"{goto(0, Hc + 1)}Frame: {frame:6d} | Intensity: {args.intensity:.2f}"
                    if args.style:
                        status += f" | Style: {args.style}"
                    sys.stdout.write(status + "\x1b[K")  # Clear to end of line

                sys.stdout.flush()

            if args.delay:
                time.sleep(args.delay)

    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write(goto(0, Hc + 2) + reset_color() + show_cursor() + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
