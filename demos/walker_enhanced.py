#!/usr/bin/env python3
"""
Enhanced Probabilistic Walker with Connection Logic and Perturbative Events

Combines:
1. NESW connection tracking (like the original connector walkers)
2. Probabilistic glyph selection from database
3. Perturbative intensity events (bursts, calms, waves)

The walker maintains a grid of connection masks (N/E/S/W bits) and uses
the probabilistic picker to SELECT the character to display, varying by
intensity and style over time through events.
"""
import argparse
import math
import random
import shutil
import sys
import time
from pathlib import Path
from typing import List, Tuple

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


class IntensityEvent:
    """Perturbative event that modulates walker intensity."""
    def __init__(self, name: str, duration: int, intensity_mod: float, style_filter: str = None):
        self.name = name
        self.duration = duration
        self.intensity_mod = intensity_mod  # Additive modifier to base intensity
        self.style_filter = style_filter
        self.remaining = duration

    def tick(self):
        """Advance event by one frame."""
        self.remaining -= 1

    def is_active(self):
        """Check if event is still active."""
        return self.remaining > 0

    def __repr__(self):
        return f"{self.name}({self.remaining}/{self.duration})"


class EventSystem:
    """Manages perturbative intensity events."""
    def __init__(self):
        self.active_events: List[IntensityEvent] = []
        self.base_intensity = 0.5

    def update(self, frame: int):
        """Update events and possibly spawn new ones."""
        # Tick active events
        for event in self.active_events:
            event.tick()

        # Remove expired events
        self.active_events = [e for e in self.active_events if e.is_active()]

        # Randomly spawn new events
        if random.random() < 0.01:  # 1% chance per frame
            self.spawn_random_event()

    def spawn_random_event(self):
        """Spawn a random perturbative event."""
        event_type = random.choice([
            ("Energy Burst", 50, 0.4, "arrow"),
            ("Calm Period", 80, -0.3, "line"),
            ("Heavy Wave", 60, 0.3, None),
            ("Light Shimmer", 40, -0.2, "braille"),
            ("Connector Storm", 70, 0.2, "connector"),
        ])
        name, duration, mod, style = event_type
        event = IntensityEvent(name, duration, mod, style)
        self.active_events.append(event)

    def get_intensity(self, base: float) -> float:
        """Get modified intensity based on active events."""
        total_mod = sum(e.intensity_mod for e in self.active_events)
        return clamp(base + total_mod, 0.0, 1.0)

    def get_style_filter(self) -> str:
        """Get active style filter (if any)."""
        for event in self.active_events:
            if event.style_filter:
                return event.style_filter
        return None

    def get_status(self) -> str:
        """Get status string for display."""
        if not self.active_events:
            return "Normal"
        return " | ".join(str(e) for e in self.active_events)


class ConnectorGrid:
    """Maintains NESW connection masks for each cell."""
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.grid: List[List[int]] = [[0] * width for _ in range(height)]

    def get(self, x: int, y: int) -> int:
        """Get connection mask at position."""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y][x]
        return 0

    def set(self, x: int, y: int, mask: int):
        """Set connection mask at position."""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[y][x] = mask

    def add_connection(self, x: int, y: int, direction: Direction):
        """Add a connection in the given direction."""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[y][x] |= direction


def main():
    ap = argparse.ArgumentParser(description="Enhanced probabilistic walker with events")
    ap.add_argument("--database", default="glyph_database_full.json",
                   help="Glyph database JSON")
    ap.add_argument("--base-intensity", type=float, default=0.5,
                   help="Base intensity before event modulation")
    ap.add_argument("--events", action="store_true", default=True,
                   help="Enable perturbative events")
    ap.add_argument("--no-events", action="store_false", dest="events",
                   help="Disable events")
    ap.add_argument("--delay", type=float, default=0.0,
                   help="Seconds between batches")
    ap.add_argument("--batch", type=int, default=300,
                   help="Moves per flush")
    ap.add_argument("--wrap", action="store_true",
                   help="Wrap at edges")
    ap.add_argument("--no-color", action="store_true",
                   help="Disable colors")
    ap.add_argument("--show-status", action="store_true", default=True,
                   help="Show event status")
    args = ap.parse_args()

    # Load database
    try:
        picker = GlyphPicker.from_json(args.database)
        print(f"Loaded {len(picker)} glyphs from {args.database}")
    except FileNotFoundError:
        print(f"Error: {args.database} not found!")
        print("Run: python3 tools/build_comprehensive_db.py --all-ranges")
        sys.exit(1)

    # Terminal setup
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    cols, rows = shutil.get_terminal_size(fallback=(100, 30))
    Wc = cols
    Hc = rows - 2  # Leave room for status line

    # Initialize grid
    grid = ConnectorGrid(Wc, Hc)

    sys.stdout.write(hide_cursor() + clear_screen())
    sys.stdout.flush()

    # Walker state
    x, y = Wc // 2, Hc // 2
    heading = Direction.E

    # Color state
    r, g, b = random.randint(100, 255), random.randint(100, 255), random.randint(100, 255)

    # Event system
    events = EventSystem()
    events.base_intensity = args.base_intensity

    frame = 0

    try:
        while True:
            out = []

            # Update events
            if args.events:
                events.update(frame)

            for _ in range(args.batch):
                # Get current intensity from events
                if args.events:
                    intensity = events.get_intensity(events.base_intensity)
                    style_filter = events.get_style_filter()
                else:
                    intensity = args.base_intensity
                    style_filter = None

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
                    intensity=intensity,
                    style=style_filter
                )
                next_char = picker.get(
                    direction=next_dir,
                    intensity=intensity,
                    style=style_filter
                )

                # Color variation
                if frame % 20 == 0 and not args.no_color:
                    r = clamp(r + random.randint(-20, 20), 80, 255)
                    g = clamp(g + random.randint(-20, 20), 80, 255)
                    b = clamp(b + random.randint(-20, 20), 80, 255)

                color = color_rgb(r, g, b) if not args.no_color else ""

                # Draw both cells
                out.append(f"{color}{goto(x, y)}{cur_char}{goto(nx, ny)}{next_char}{reset_color()}")

                x, y = nx, ny
                frame += 1

            # Flush output
            if out:
                sys.stdout.write("".join(out))

                # Show status line
                if args.show_status:
                    status = events.get_status()
                    status_line = f"{goto(0, Hc + 1)}Intensity: {intensity:.2f} | Events: {status}"
                    sys.stdout.write(status_line + "\x1b[K")  # Clear to end of line

                sys.stdout.flush()

            if args.delay:
                time.sleep(args.delay)

    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write(goto(0, Hc + 2) + reset_color() + show_cursor())
        sys.stdout.flush()


if __name__ == "__main__":
    main()
