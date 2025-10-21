#!/usr/bin/env python3
"""
Glyph data structure for directional character mapping.
"""
from dataclasses import dataclass, field
from typing import List, Set, Optional
from .direction import Direction, string_to_direction, direction_to_string


@dataclass
class GlyphInfo:
    """Information about a single glyph/character.

    Attributes:
        char: The Unicode character itself
        codepoint: Unicode codepoint (e.g., "U+2192")
        directions: Set of Direction flags this glyph visually represents
        intensity: Visual weight/intensity from 0.0 (lightest) to 1.0 (heaviest)
        styles: Set of style tags (e.g., {"arrow", "geometric"})
        weight: Categorical weight: "light", "medium", "heavy"
    """
    char: str
    codepoint: str
    directions: Direction = Direction.NONE
    intensity: float = 0.5
    styles: Set[str] = field(default_factory=set)
    weight: str = "medium"  # light, medium, heavy

    def __post_init__(self):
        """Validate and normalize fields."""
        if not isinstance(self.styles, set):
            self.styles = set(self.styles) if self.styles else set()

        # Clamp intensity
        self.intensity = max(0.0, min(1.0, self.intensity))

        # Normalize weight
        if self.weight not in ("light", "medium", "heavy"):
            self.weight = "medium"

    def matches_direction(self, target: Direction, exact: bool = False) -> bool:
        """Check if this glyph matches the target direction.

        Args:
            target: Direction to match
            exact: If True, must match exactly. If False, any overlap counts.

        Returns:
            True if direction matches criteria
        """
        if exact:
            return self.directions == target
        else:
            # Check if there's any overlap
            return bool(self.directions & target)

    def matches_intensity(self, min_val: float, max_val: float) -> bool:
        """Check if intensity is in range [min_val, max_val]."""
        return min_val <= self.intensity <= max_val

    def matches_style(self, style: str) -> bool:
        """Check if this glyph has the given style tag."""
        return style in self.styles

    def matches_weight(self, weight: str) -> bool:
        """Check if this glyph has the given categorical weight."""
        return self.weight == weight

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dictionary."""
        return {
            "char": self.char,
            "codepoint": self.codepoint,
            "directions": direction_to_string(self.directions),
            "intensity": self.intensity,
            "styles": sorted(list(self.styles)),
            "weight": self.weight,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GlyphInfo":
        """Create GlyphInfo from dictionary."""
        # Parse directions from string
        dir_str = data.get("directions", "")
        if isinstance(dir_str, str):
            directions = string_to_direction(dir_str)
        else:
            directions = Direction.NONE

        return cls(
            char=data["char"],
            codepoint=data["codepoint"],
            directions=directions,
            intensity=data.get("intensity", 0.5),
            styles=set(data.get("styles", [])),
            weight=data.get("weight", "medium"),
        )

    def __repr__(self) -> str:
        dir_str = direction_to_string(self.directions)
        styles_str = ",".join(sorted(self.styles))
        return (
            f"GlyphInfo('{self.char}', {self.codepoint}, "
            f"dir={dir_str}, intensity={self.intensity:.2f}, "
            f"styles=[{styles_str}], weight={self.weight})"
        )
