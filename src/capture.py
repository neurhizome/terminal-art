#!/usr/bin/env python3
"""
capture.py - Terminal screenshot system for pattern documentation

Captures the current terminal state with ANSI codes intact.
Files can be replayed with `cat filename.ans` to see exactly what was rendered.

Perfect for building a visual museum of discoveries!
"""

import sys
import os
from datetime import datetime
from typing import Optional


class TerminalCapture:
    """
    Capture terminal output for later replay.

    Saves current screen state to file with ANSI codes intact.
    Files can be viewed with: cat filename.ans
    """

    def __init__(self, museum_dir: str = "museum"):
        """
        Initialize capture system.

        Args:
            museum_dir: Directory to save captures
        """
        self.museum_dir = museum_dir
        os.makedirs(museum_dir, exist_ok=True)

    def capture(self,
                output: str,
                name: str,
                script: Optional[str] = None,
                seed: Optional[int] = None,
                params: Optional[dict] = None,
                tick: Optional[int] = None,
                description: Optional[str] = None) -> str:
        """
        Capture terminal output to file.

        Args:
            output: Raw terminal output with ANSI codes
            name: Short name for this capture
            script: Which script generated this
            seed: Random seed (if reproducible)
            params: Key parameters
            tick: Tick number when captured
            description: What makes this interesting

        Returns:
            Path to saved file
        """
        # Generate filename
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        safe_name = name.replace(" ", "_").lower()
        filename = f"{timestamp}_{safe_name}.ans"
        filepath = os.path.join(self.museum_dir, filename)

        # Build header with metadata
        header_lines = [
            f"# CAPTURE: {name}",
            f"# Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        ]

        if script:
            header_lines.append(f"# Script: {script}")
        if seed is not None:
            header_lines.append(f"# Seed: {seed}")
        if params:
            params_str = ", ".join(f"{k}={v}" for k, v in params.items())
            header_lines.append(f"# Params: {params_str}")
        if tick is not None:
            header_lines.append(f"# Tick: {tick}")
        if description:
            header_lines.append(f"# Description: {description}")

        header_lines.append(f"#")
        header_lines.append(f"# To view: cat {filepath}")
        header_lines.append(f"#")

        header = "\n".join(header_lines) + "\n\n"

        # Save with header
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(header)
            f.write(output)

        return filepath

    def capture_frame(self,
                     stage,
                     name: str,
                     **metadata) -> str:
        """
        Capture current terminal stage state.

        Args:
            stage: TerminalStage instance
            name: Short name for capture
            **metadata: Additional metadata (script, seed, params, etc.)

        Returns:
            Path to saved file
        """
        # Render current state to string
        output_lines = []

        # Add clear screen and position cursor at top
        output_lines.append("\x1b[2J\x1b[H")

        # Render all cells
        for y in range(stage.height):
            for x in range(stage.width):
                cell = stage.cells[y][x]
                output_lines.append(f"\x1b[{y+1};{x+1}H{cell.render()}")

        output = "".join(output_lines)

        return self.capture(output, name, **metadata)


# Global instance
_capture = None

def get_capture(museum_dir: str = "museum") -> TerminalCapture:
    """Get global capture instance"""
    global _capture
    if _capture is None:
        _capture = TerminalCapture(museum_dir)
    return _capture


def quick_capture(stage, name: str, description: str = "", **metadata) -> str:
    """
    Quick capture of current state.

    Usage:
        from src.capture import quick_capture

        # During experiment
        quick_capture(stage, "rainbow_spiral",
                     description="Perfect spiral formation!",
                     seed=42, tick=1523)

    Returns:
        Path to saved file
    """
    capture = get_capture()
    metadata['description'] = description
    return capture.capture_frame(stage, name, **metadata)


def browse_museum(museum_dir: str = "museum"):
    """
    List all captures in museum.

    Prints a browseable index of captured patterns.
    """
    if not os.path.exists(museum_dir):
        print(f"Museum directory '{museum_dir}' doesn't exist yet.")
        print("Capture some patterns first!")
        return

    captures = sorted([f for f in os.listdir(museum_dir) if f.endswith('.ans')])

    if not captures:
        print(f"No captures in {museum_dir} yet.")
        print("Start exploring and capture cool patterns!")
        return

    print(f"\n📸 Museum: {len(captures)} captures\n")
    print("=" * 70)

    for filename in captures:
        filepath = os.path.join(museum_dir, filename)

        # Read metadata from header
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        metadata = {}
        for line in lines:
            if not line.startswith('#'):
                break
            if ':' in line:
                key, value = line[1:].split(':', 1)
                metadata[key.strip()] = value.strip()

        # Print entry
        name = metadata.get('CAPTURE', filename)
        date = metadata.get('Date', 'Unknown')
        desc = metadata.get('Description', '')

        print(f"\n{name}")
        print(f"  Date: {date}")
        if desc:
            print(f"  {desc}")
        print(f"  View: cat {filepath}")

    print("\n" + "=" * 70)
    print(f"\nTo view a capture: cat {museum_dir}/[filename]\n")


if __name__ == '__main__':
    """Browse the museum"""
    import sys

    if len(sys.argv) > 1:
        museum_dir = sys.argv[1]
    else:
        museum_dir = "museum"

    browse_museum(museum_dir)
