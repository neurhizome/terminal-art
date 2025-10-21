"""
Directional glyph mapping system for probabilistic character selection.

This module provides a system for categorizing Unicode characters by their
visual properties (direction, intensity, style) and selecting them probabilistically
for use in terminal-based animations and walkers.

Example:
    from src.glyphs import GlyphPicker, Direction

    picker = GlyphPicker.from_json("glyph_database.json")
    char = picker.get(direction=Direction.E, intensity=0.7)
    print(f"Heading east: {char}")
"""

from .direction import Direction, OPPOSITES, direction_to_vector, direction_from_vector
from .glyph_data import GlyphInfo
from .picker import GlyphPicker

__all__ = [
    "Direction",
    "OPPOSITES",
    "direction_to_vector",
    "direction_from_vector",
    "GlyphInfo",
    "GlyphPicker",
]
