#!/usr/bin/env python3
"""
Probabilistic glyph picker for directional character selection.
"""
import json
import random
from pathlib import Path
from typing import List, Optional, Set, Tuple
from .direction import Direction
from .glyph_data import GlyphInfo


class GlyphPicker:
    """Probabilistic selector for directional glyphs.

    Maintains a database of glyphs with their visual properties and provides
    weighted random selection based on criteria like direction, intensity, and style.
    """

    def __init__(self):
        self.glyphs: List[GlyphInfo] = []
        self._by_direction: dict[Direction, List[GlyphInfo]] = {}
        self._by_style: dict[str, List[GlyphInfo]] = {}
        self._by_weight: dict[str, List[GlyphInfo]] = {}

    def add_glyph(self, glyph: GlyphInfo):
        """Add a glyph to the database and update indices."""
        self.glyphs.append(glyph)

        # Index by direction
        if glyph.directions not in self._by_direction:
            self._by_direction[glyph.directions] = []
        self._by_direction[glyph.directions].append(glyph)

        # Index by styles
        for style in glyph.styles:
            if style not in self._by_style:
                self._by_style[style] = []
            self._by_style[style].append(glyph)

        # Index by weight
        if glyph.weight not in self._by_weight:
            self._by_weight[glyph.weight] = []
        self._by_weight[glyph.weight].append(glyph)

    def get(
        self,
        direction: Optional[Direction] = None,
        intensity: Optional[float] = None,
        intensity_range: Optional[Tuple[float, float]] = None,
        style: Optional[str] = None,
        weight: Optional[str] = None,
        exact_direction: bool = False,
    ) -> str:
        """Get a random glyph matching the given criteria.

        Args:
            direction: Required direction(s)
            intensity: Target intensity (will select within ±0.2)
            intensity_range: Tuple of (min, max) intensity
            style: Required style tag
            weight: Required weight category
            exact_direction: If True, direction must match exactly

        Returns:
            A Unicode character matching criteria, or " " if none found
        """
        candidates = self._filter_glyphs(
            direction=direction,
            intensity=intensity,
            intensity_range=intensity_range,
            style=style,
            weight=weight,
            exact_direction=exact_direction,
        )

        if not candidates:
            return " "  # fallback to space

        # Weighted random selection based on intensity match
        if intensity is not None and len(candidates) > 1:
            # Weight by how close intensity is to target
            weights = []
            for g in candidates:
                distance = abs(g.intensity - intensity)
                # Inverse distance weighting (closer = higher weight)
                w = 1.0 / (1.0 + distance * 5.0)
                weights.append(w)

            return random.choices(candidates, weights=weights, k=1)[0].char
        else:
            # Uniform random selection
            return random.choice(candidates).char

    def get_all(
        self,
        direction: Optional[Direction] = None,
        intensity: Optional[float] = None,
        intensity_range: Optional[Tuple[float, float]] = None,
        style: Optional[str] = None,
        weight: Optional[str] = None,
        exact_direction: bool = False,
    ) -> List[GlyphInfo]:
        """Get all glyphs matching the criteria (not just one random selection)."""
        return self._filter_glyphs(
            direction=direction,
            intensity=intensity,
            intensity_range=intensity_range,
            style=style,
            weight=weight,
            exact_direction=exact_direction,
        )

    def _filter_glyphs(
        self,
        direction: Optional[Direction] = None,
        intensity: Optional[float] = None,
        intensity_range: Optional[Tuple[float, float]] = None,
        style: Optional[str] = None,
        weight: Optional[str] = None,
        exact_direction: bool = False,
    ) -> List[GlyphInfo]:
        """Filter glyphs based on criteria."""
        # Start with all glyphs
        candidates = list(self.glyphs)

        # Filter by direction
        if direction is not None:
            candidates = [
                g for g in candidates
                if g.matches_direction(direction, exact=exact_direction)
            ]

        # Filter by intensity
        if intensity is not None:
            # Default to ±0.2 range around target
            min_i = max(0.0, intensity - 0.2)
            max_i = min(1.0, intensity + 0.2)
            candidates = [
                g for g in candidates
                if g.matches_intensity(min_i, max_i)
            ]

        # Filter by intensity range
        if intensity_range is not None:
            min_i, max_i = intensity_range
            candidates = [
                g for g in candidates
                if g.matches_intensity(min_i, max_i)
            ]

        # Filter by style
        if style is not None:
            candidates = [
                g for g in candidates
                if g.matches_style(style)
            ]

        # Filter by weight
        if weight is not None:
            candidates = [
                g for g in candidates
                if g.matches_weight(weight)
            ]

        return candidates

    def save_json(self, filepath: str):
        """Save glyph database to JSON file."""
        data = {
            "glyphs": [g.to_dict() for g in self.glyphs]
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, filepath: str) -> "GlyphPicker":
        """Load glyph database from JSON file."""
        picker = cls()
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        for glyph_dict in data.get("glyphs", []):
            glyph = GlyphInfo.from_dict(glyph_dict)
            picker.add_glyph(glyph)

        return picker

    def __len__(self) -> int:
        return len(self.glyphs)

    def __repr__(self) -> str:
        return f"GlyphPicker({len(self.glyphs)} glyphs)"
