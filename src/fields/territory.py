#!/usr/bin/env python3
"""
territory.py - Chunked ownership tracking with memetic colors

Tracks which walkers have visited each region.
Territory color emerges from visitor history weighted by vigor.

Chunked implementation for performance (don't track every cell individually).
"""

import colorsys
import math
from typing import Any, Dict, List, Tuple, Optional, TYPE_CHECKING
from .base import Field

if TYPE_CHECKING:
    from src.automata.walker import Walker
    from src.genetics import Genome


class TerritoryChunk:
    """
    Represents ownership of a grid region.

    Tracks visitor history with weighted contribution by vigor.
    """

    def __init__(self):
        self.visitors: Dict[int, float] = {}  # walker_id -> weight
        self.total_weight = 0.0
        self.cached_color: Optional[Tuple[float, float, float]] = None  # (h, s, v)
        self.dirty = True

    def add_visitor(self, walker_id: int, walker_hue: float, vigor: float):
        """
        Record walker visit with vigor-weighted contribution.

        Args:
            walker_id: Unique walker identifier
            walker_hue: Walker's hue [0, 1)
            vigor: Walker's fitness weight
        """
        if walker_id not in self.visitors:
            self.visitors[walker_id] = 0.0

        self.visitors[walker_id] += vigor
        self.total_weight += vigor
        self.dirty = True

    def get_color(self, walker_genomes: Dict[int, 'Genome']) -> Tuple[int, int, int]:
        """
        Compute emergent color from visitor history.

        Args:
            walker_genomes: Map of walker_id -> Genome for color lookup

        Returns:
            (r, g, b) in [0, 255]
        """
        if self.total_weight == 0:
            return (20, 20, 25)  # Empty territory color

        # Use cached color if not dirty
        if not self.dirty and self.cached_color is not None:
            h, s, v = self.cached_color
            r, g, b = colorsys.hsv_to_rgb(h, s, v)
            return (int(r * 255), int(g * 255), int(b * 255))

        # Compute weighted circular mean of hues
        cos_sum = 0.0
        sin_sum = 0.0

        for walker_id, weight in self.visitors.items():
            if walker_id in walker_genomes:
                genome = walker_genomes[walker_id]
                h = genome.color_h
                cos_sum += weight * math.cos(2 * math.pi * h)
                sin_sum += weight * math.sin(2 * math.pi * h)

        mean_hue = math.atan2(sin_sum, cos_sum) / (2 * math.pi)
        mean_hue = mean_hue % 1.0

        # Saturation based on dominance (high weight concentration = high sat)
        max_weight = max(self.visitors.values()) if self.visitors else 0
        dominance = max_weight / self.total_weight if self.total_weight > 0 else 0
        saturation = 0.3 + dominance * 0.5  # [0.3, 0.8]

        # Value based on total activity
        value = min(0.9, 0.3 + self.total_weight / 100.0)

        # Cache result
        self.cached_color = (mean_hue, saturation, value)
        self.dirty = False

        r, g, b = colorsys.hsv_to_rgb(mean_hue, saturation, value)
        return (int(r * 255), int(g * 255), int(b * 255))


class TerritoryField(Field):
    """
    Chunked territory tracking with emergent colors.

    Grid is divided into chunks. Each chunk tracks visitor history.
    Territory colors emerge from weighted blending of visitor genomes.
    """

    def __init__(self, width: int, height: int, chunk_size: int = 8):
        """
        Initialize territory field.

        Args:
            width, height: Grid dimensions
            chunk_size: Size of territory chunks (larger = better performance)
        """
        super().__init__(width, height)
        self.chunk_size = chunk_size
        self.chunks_wide = (width + chunk_size - 1) // chunk_size
        self.chunks_high = (height + chunk_size - 1) // chunk_size

        # Grid of chunks
        self.chunks = [
            [TerritoryChunk() for _ in range(self.chunks_wide)]
            for _ in range(self.chunks_high)
        ]

        # Track active walkers for color lookup
        self.walker_genomes: Dict[int, 'Genome'] = {}

    def _get_chunk(self, x: int, y: int) -> Optional[TerritoryChunk]:
        """Get chunk containing position"""
        cx = x // self.chunk_size
        cy = y // self.chunk_size
        if 0 <= cx < self.chunks_wide and 0 <= cy < self.chunks_high:
            return self.chunks[cy][cx]
        return None

    def claim(self, walker: 'Walker'):
        """
        Record walker visit at current position.

        Args:
            walker: Walker claiming territory
        """
        chunk = self._get_chunk(walker.x, walker.y)
        if chunk:
            walker_id = id(walker)
            chunk.add_visitor(walker_id, walker.genome.color_h, walker.vigor)

            # Update genome registry
            self.walker_genomes[walker_id] = walker.genome

    def get(self, x: int, y: int) -> Optional[TerritoryChunk]:
        """Get chunk at position"""
        return self._get_chunk(x, y)

    def set(self, x: int, y: int, value: Any):
        """Not implemented for territory field"""
        pass

    def update(self):
        """No dynamics - territory persists"""
        pass

    def clear(self):
        """Reset all territories"""
        self.chunks = [
            [TerritoryChunk() for _ in range(self.chunks_wide)]
            for _ in range(self.chunks_high)
        ]
        self.walker_genomes.clear()

    def prune_genomes(self, active_walker_ids: set):
        """
        Remove stale genome references for dead walkers.

        Args:
            active_walker_ids: Set of currently alive walker IDs
        """
        self.walker_genomes = {
            wid: genome for wid, genome in self.walker_genomes.items()
            if wid in active_walker_ids
        }

    def render(self) -> List[List[Tuple[str, Tuple[int, int, int], Tuple[int, int, int]]]]:
        """
        Render territory colors.

        Returns:
            Grid of (char, fg_color, bg_color) - territory shown as background
        """
        result = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                chunk = self._get_chunk(x, y)
                if chunk:
                    bg_color = chunk.get_color(self.walker_genomes)
                else:
                    bg_color = (20, 20, 25)

                # Show territory as background color
                char = ' '
                fg_color = (255, 255, 255)

                # Optional: Show chunk boundaries
                if x % self.chunk_size == 0 or y % self.chunk_size == 0:
                    char = '·'
                    fg_color = (60, 60, 60)

                row.append((char, fg_color, bg_color))
            result.append(row)
        return result

    def get_stats(self) -> Dict:
        """
        Get territory statistics.

        Returns:
            Dict with total_chunks, active_chunks, total_weight
        """
        total_chunks = self.chunks_wide * self.chunks_high
        active_chunks = sum(
            1 for row in self.chunks for chunk in row
            if chunk.total_weight > 0
        )
        total_weight = sum(
            chunk.total_weight for row in self.chunks for chunk in row
        )

        return {
            'total_chunks': total_chunks,
            'active_chunks': active_chunks,
            'total_weight': total_weight,
            'coverage': active_chunks / total_chunks if total_chunks > 0 else 0,
        }
