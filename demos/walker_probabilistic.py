#!/usr/bin/env python3
"""
Probabilistic Directional Walker

Uses the new GlyphPicker system to select characters based on:
- Direction of movement (N/E/S/W)
- Intensity (varies with speed or "energy")
- Style (can mix arrows, connectors, etc.)

This creates more organic, varied walker trails compared to static connector maps!
"""
import argparse
import random
import shutil
import sys
import time
from pathlib import Path
from typing import Tuple

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.glyphs import GlyphPicker, Direction, direction_from_vector

# Color helpers
def color_seq(r: int, g: int, b: int) -> str:
    """Generate 24-bit ANSI color sequence."""
    return f"\x1b[38;2;{r};{g};{b}m"


def clamp(v, lo, hi):
    """Clamp value between lo and hi."""
    return lo if v < lo else hi if v > hi else v


class IntensityOscillator:
    """Oscillates intensity over time for visual variety."""
    def __init__(self, base: float = 0.5, amplitude: float = 0.3, speed: float = 0.05):
        self.base = base
        self.amplitude = amplitude
        self.speed = speed
        self.phase = random.random() * 6.28

    def get(self, frame: int) -> float:
        """Get intensity for current frame."""
        import math
        intensity = self.base + self.amplitude * math.sin(self.phase + frame * self.speed)
        return clamp(intensity, 0.0, 1.0)


def main():
    ap = argparse.ArgumentParser(description="Probabilistic directional walker demo")
    ap.add_argument("--database", default="glyph_database.json", help="Glyph database JSON")
    ap.add_argument("--style", default="connector", help="Glyph style filter (connector, arrow, organic)")
    ap.add_argument("--intensity-base", type=float, default=0.5, help="Base intensity (0.0-1.0)")
    ap.add_argument("--intensity-var", type=float, default=0.3, help="Intensity variation amplitude")
    ap.add_argument("--delay", type=float, default=0.0, help="Seconds between batches")
    ap.add_argument("--steps", type=int, default=0, help="Total moves (0=infinite)")
    ap.add_argument("--batch", type=int, default=600, help="Moves per flush")
    ap.add_argument("--wrap", action="store_true", help="Wrap at edges instead of bouncing")
    ap.add_argument("--no-color", action="store_true", help="Disable colors")
    args = ap.parse_args()

    # Load glyph database
    try:
        picker = GlyphPicker.from_json(args.database)
        print(f"Loaded {len(picker)} glyphs from {args.database}")
    except FileNotFoundError:
        print(f"Error: {args.database} not found!")
        print("Run: python3 tools/glyph_categorizer.py --quick-start")
        sys.exit(1)

    # Terminal setup
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    cols, rows = shutil.get_terminal_size(fallback=(100, 30))
    Wc, Hc = cols, rows - 1 if rows > 1 else rows
    Wc = max(10, Wc)
    Hc = max(5, Hc)

    hide = "\x1b[?25l"
    show = "\x1b[?25h"
    clear = "\x1b[2J"
    reset = "\x1b[0m"

    sys.stdout.write(hide + clear)
    sys.stdout.flush()

    # Walker state
    x, y = Wc // 2, Hc // 2
    heading = Direction.E

    # Color state
    r, g, b = random.randint(100, 255), random.randint(100, 255), random.randint(100, 255)

    # Intensity oscillator for visual variety
    intensity_osc = IntensityOscillator(
        base=args.intensity_base,
        amplitude=args.intensity_var,
        speed=0.03
    )

    steps_done = 0
    frame = 0

    try:
        while True:
            out = []

            for _ in range(args.batch):
                # Get current intensity
                intensity = intensity_osc.get(frame)

                # Pick next direction (no backtracking)
                opposite = {Direction.N: Direction.S, Direction.S: Direction.N,
                           Direction.E: Direction.W, Direction.W: Direction.E}
                choices = [d for d in [Direction.N, Direction.E, Direction.S, Direction.W]
                          if d != opposite.get(heading, Direction.NONE)]
                heading = random.choice(choices)

                # Get glyph for this direction and intensity
                glyph = picker.get(
                    direction=heading,
                    intensity=intensity,
                    style=args.style if args.style != "all" else None
                )

                # Move
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
                    if nx < 0 or nx >= Wc:
                        heading = opposite[heading]
                        dx, dy = -dx, -dy
                        nx = clamp(x + dx, 0, Wc - 1)
                    if ny < 0 or ny >= Hc:
                        heading = opposite[heading]
                        dx, dy = -dx, -dy
                        ny = clamp(y + dy, 0, Hc - 1)

                # Color variation
                if frame % 10 == 0 and not args.no_color:
                    r = clamp(r + random.randint(-15, 15), 80, 255)
                    g = clamp(g + random.randint(-15, 15), 80, 255)
                    b = clamp(b + random.randint(-15, 15), 80, 255)

                color = color_seq(r, g, b) if not args.no_color else ""

                # Draw glyph at current position
                out.append(f"{color}\x1b[{y+1};{x+1}H{glyph}{reset}")

                x, y = nx, ny
                steps_done += 1
                frame += 1

                if args.steps and steps_done >= args.steps:
                    break

            # Flush output
            if out:
                sys.stdout.write("".join(out))
                sys.stdout.flush()

            if args.steps and steps_done >= args.steps:
                break

            if args.delay:
                time.sleep(args.delay)

            # Resize handling
            new_cols, new_rows = shutil.get_terminal_size(fallback=(cols, rows))
            if new_cols != cols or new_rows != rows:
                cols, rows = new_cols, new_rows
                Wc, Hc = cols, rows - 1 if rows > 1 else rows
                Wc = max(10, Wc)
                Hc = max(5, Hc)
                x = min(max(0, x), Wc - 1)
                y = min(max(0, y), Hc - 1)
                sys.stdout.write(clear)
                sys.stdout.flush()

    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write(f"\x1b[{Hc+1};1H{reset}" + show)
        sys.stdout.flush()


if __name__ == "__main__":
    main()
