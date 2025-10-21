#!/usr/bin/env python3
"""
terminal_stage.py - A robust full-screen terminal canvas for cellular simulations

Provides a clean abstraction for:

- Terminal size detection & resize handling
- Efficient cell-by-cell updates with cursor positioning
- Double-buffering to eliminate flicker
- 24-bit color with anti-color generation
- Cell object model with arbitrary attributes

This is the STAGE. Simulations are PLUGINS that run on it.
"""

import sys
import shutil
import time
import signal
import atexit
import tty
import termios
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Tuple, Dict
import colorsys
import random
import math

# ===================== TERMINAL CONTROL =====================

class TerminalStage:
    """Manages full-screen terminal canvas with efficient updates"""

    def __init__(self):
        self.width = 0
        self.height = 0
        self.cells: list[list[Optional['CellState']]] = []
        self.prev_render: list[list[str]] = []  # for dirty checking
        self.initialized = False
        
        # Terminal state preservation
        self.old_term_settings = None
        
    def __enter__(self):
        self.setup()
        return self
        
    def __exit__(self, *args):
        self.teardown()
        
    def setup(self):
        """Initialize terminal for full-screen rendering"""
        if self.initialized:
            return
            
        # Save terminal settings
        try:
            self.old_term_settings = termios.tcgetattr(sys.stdin.fileno())
        except:
            pass
            
        # Register cleanup
        atexit.register(self.teardown)
        signal.signal(signal.SIGWINCH, self._handle_resize)
        
        # Enter alternate screen buffer + hide cursor
        sys.stdout.write("\x1b[?1049h")  # alt screen
        sys.stdout.write("\x1b[?25l")     # hide cursor
        sys.stdout.write("\x1b[2J")       # clear screen
        sys.stdout.flush()
        
        # Configure UTF-8
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except:
            pass
            
        self._update_dimensions()
        self.initialized = True
        
    def teardown(self):
        """Restore terminal state"""
        if not self.initialized:
            return
            
        # Show cursor + exit alt screen
        sys.stdout.write("\x1b[?25h")
        sys.stdout.write("\x1b[?1049l")
        sys.stdout.write("\x1b[0m")
        sys.stdout.flush()
        
        # Restore terminal settings
        if self.old_term_settings:
            try:
                termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, 
                                 self.old_term_settings)
            except:
                pass
                
        self.initialized = False
        
    def _handle_resize(self, signum, frame):
        """Handle terminal resize signal"""
        old_w, old_h = self.width, self.height
        self._update_dimensions()
        if (self.width, self.height) != (old_w, old_h):
            self._resize_grid()
            
    def _update_dimensions(self):
        """Query current terminal size"""
        cols, rows = shutil.get_terminal_size(fallback=(80, 24))
        self.width = max(1, cols)
        self.height = max(1, rows)
        
    def _resize_grid(self):
        """Resize cell grid when terminal dimensions change"""
        new_cells = [[None for _ in range(self.width)] 
                     for _ in range(self.height)]
        new_prev = [["" for _ in range(self.width)] 
                    for _ in range(self.height)]
        
        # Copy over existing cells
        for y in range(min(len(self.cells), self.height)):
            for x in range(min(len(self.cells[0]) if self.cells else 0, self.width)):
                if y < len(self.cells) and x < len(self.cells[y]):
                    new_cells[y][x] = self.cells[y][x]
                if y < len(self.prev_render) and x < len(self.prev_render[y]):
                    new_prev[y][x] = self.prev_render[y][x]
                    
        self.cells = new_cells
        self.prev_render = new_prev
        
        # Force full redraw after resize
        sys.stdout.write("\x1b[2J")
        sys.stdout.flush()
        
    def init_grid(self):
        """Initialize empty cell grid"""
        self.cells = [[None for _ in range(self.width)] 
                      for _ in range(self.height)]
        self.prev_render = [["" for _ in range(self.width)] 
                           for _ in range(self.height)]
                           
    def get_cell(self, x: int, y: int) -> Optional['CellState']:
        """Get cell at position (with bounds checking)"""
        if 0 <= y < self.height and 0 <= x < self.width:
            return self.cells[y][x]
        return None
        
    def set_cell(self, x: int, y: int, cell: Optional['CellState']):
        """Set cell at position (with bounds checking)"""
        if 0 <= y < self.height and 0 <= x < self.width:
            self.cells[y][x] = cell
            
    def render(self, force_full: bool = False):
        """Render all dirty cells to screen"""
        output = []
        
        for y in range(self.height):
            for x in range(self.width):
                cell = self.cells[y][x]
                
                if cell is None:
                    rendered = " "
                else:
                    rendered = cell.render()
                
                # Only update if changed (or forced)
                if force_full or rendered != self.prev_render[y][x]:
                    # Move cursor and write
                    output.append(f"\x1b[{y+1};{x+1}H{rendered}")
                    self.prev_render[y][x] = rendered
                    
        if output:
            sys.stdout.write("".join(output))
            sys.stdout.flush()
            
    def clear(self):
        """Clear all cells"""
        self.cells = [[None for _ in range(self.width)] 
                      for _ in range(self.height)]
        self.render(force_full=True)

# ===================== COLOR UTILITIES =====================

def clamp01(x: float) -> float:
    """Clamp to [0, 1]"""
    return max(0.0, min(1.0, x))

def clamp8(x: float) -> int:
    """Clamp to [0, 255]"""
    return max(0, min(255, int(x)))

def rgb_tuple(r: float, g: float, b: float) -> Tuple[int, int, int]:
    """Convert float RGB [0,1] to int tuple"""
    return (clamp8(r * 255), clamp8(g * 255), clamp8(b * 255))

def anti_colors_from_fg(h: float, s: float, v: float) -> Tuple[Tuple[int,int,int], Tuple[int,int,int]]:
    """Generate vivid anti-color pair from foreground HSV"""
    fg_h, fg_s, fg_v = h % 1.0, clamp01(s), clamp01(v)

    # Complementary hue
    bg_h = (fg_h + 0.5) % 1.0

    # Punch up saturation for both
    fg_s = clamp01(0.35 + 0.65 * fg_s)
    bg_s = clamp01(0.45 + 0.55 * (1.0 - fg_s))

    # Invert value for contrast
    bg_v = clamp01(0.60 + 0.40 * (1.0 - fg_v))

    rf, gf, bf = colorsys.hsv_to_rgb(fg_h, fg_s, fg_v)
    rb, gb, bb = colorsys.hsv_to_rgb(bg_h, bg_s, bg_v)

    return rgb_tuple(rf, gf, bf), rgb_tuple(rb, gb, bb)

# ===================== CELL STATE MODEL =====================

@dataclass
class CellState:
    """
    Represents one cell in the grid.
    Subclass this for domain-specific simulations.
    """
    glyph: str = "•"
    fg: Tuple[int, int, int] = (255, 255, 255)
    bg: Tuple[int, int, int] = (0, 0, 0)

    # Extensible attributes for simulations
    metadata: Dict[str, Any] = field(default_factory=dict)

    def render(self) -> str:
        """Generate ANSI escape sequence for this cell"""
        r, g, b = self.fg
        br, bg, bb = self.bg
        return f"\x1b[38;2;{r};{g};{b}m\x1b[48;2;{br};{bg};{bb}m{self.glyph}\x1b[0m"

# ===================== SIMULATION FRAMEWORK =====================

class Simulation:
    """
    Base class for simulations that run on the TerminalStage.
    Subclass this to create custom behaviors.
    """

    def __init__(self, stage: TerminalStage):
        self.stage = stage
        
    def setup(self):
        """Called once before simulation starts"""
        pass
        
    def step(self, frame: int):
        """
        Called each frame. Update cell states here.
        frame: integer frame counter
        """
        pass
        
    def run(self, fps: float = 30, max_frames: int = 0):
        """Run simulation loop"""
        self.setup()
        frame = 0
        delay = 1.0 / fps if fps > 0 else 0
        
        try:
            while True:
                start = time.time()
                
                self.step(frame)
                self.stage.render()
                
                frame += 1
                if max_frames and frame >= max_frames:
                    break
                    
                # Maintain target FPS
                elapsed = time.time() - start
                if delay > elapsed:
                    time.sleep(delay - elapsed)
                    
        except KeyboardInterrupt:
            pass

