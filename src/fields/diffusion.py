#!/usr/bin/env python3
"""
diffusion.py - Scent trail / chemical diffusion field

Values spread to neighbors and decay over time.
Walkers deposit "scent" that diffuses through space.

Classic use case: pheromone trails, gradient following, territory marking.
"""

import random
from typing import Tuple, List
from .base import ScalarField


class DiffusionField(ScalarField):
    """
    Field with diffusion and decay dynamics.

    Values spread to neighbors each tick and gradually fade.
    """

    def __init__(self, width: int, height: int,
                 diffusion_rate: float = 0.2,
                 decay_rate: float = 0.95,
                 min_threshold: float = 0.01):
        """
        Initialize diffusion field.

        Args:
            width, height: Grid dimensions
            diffusion_rate: Fraction of value that spreads to neighbors [0, 1]
            decay_rate: Fraction of value that persists each tick [0, 1]
            min_threshold: Values below this are set to 0 (optimization)
        """
        super().__init__(width, height, initial_value=0.0)
        self.diffusion_rate = diffusion_rate
        self.decay_rate = decay_rate
        self.min_threshold = min_threshold

        # Double buffer for updates
        self.next_grid = [[0.0 for _ in range(width)] for _ in range(height)]

    def deposit(self, x: int, y: int, amount: float):
        """
        Add scent/chemical at position.

        Args:
            x, y: Position
            amount: Value to add
        """
        self.add(x, y, amount)

    def gradient_at(self, x: int, y: int) -> Tuple[float, float]:
        """
        Calculate gradient vector at position.

        Args:
            x, y: Position

        Returns:
            (grad_x, grad_y) - direction of steepest increase
        """
        center = self.get(x, y)

        # Sample 4-neighborhood
        north = self.get(x, y - 1)
        south = self.get(x, y + 1)
        east = self.get(x + 1, y)
        west = self.get(x - 1, y)

        grad_x = (east - west) / 2.0
        grad_y = (south - north) / 2.0

        return (grad_x, grad_y)

    def update(self):
        """
        Apply diffusion and decay.

        Diffusion: Each cell shares portion of value with 4 neighbors.
        Decay: Values gradually fade over time.
        """
        # Copy current state to next buffer
        for y in range(self.height):
            for x in range(self.width):
                value = self.grid[y][x]

                # Decay
                value *= self.decay_rate

                # Diffusion: Share with 4-neighbors
                neighbors = [
                    (x, y - 1),  # N
                    (x + 1, y),  # E
                    (x, y + 1),  # S
                    (x - 1, y),  # W
                ]

                # Amount to diffuse
                diffuse_amount = value * self.diffusion_rate
                keep_amount = value * (1.0 - self.diffusion_rate)

                # Share equally among neighbors
                diffuse_per_neighbor = diffuse_amount / 4.0

                # Keep portion
                self.next_grid[y][x] = keep_amount

                # Diffuse to neighbors
                for nx, ny in neighbors:
                    if self.in_bounds(nx, ny):
                        self.next_grid[ny][nx] += diffuse_per_neighbor

        # Apply threshold (optimization: zero out tiny values)
        for y in range(self.height):
            for x in range(self.width):
                if self.next_grid[y][x] < self.min_threshold:
                    self.next_grid[y][x] = 0.0

        # Swap buffers
        self.grid, self.next_grid = self.next_grid, self.grid

        # Clear next buffer
        for y in range(self.height):
            for x in range(self.width):
                self.next_grid[y][x] = 0.0

    def render(self) -> List[List[Tuple[str, Tuple[int, int, int], Tuple[int, int, int]]]]:
        """
        Render as heatmap - brighter = higher concentration.

        Returns:
            Grid of (char, fg_color, bg_color)
        """
        max_val = self.max_value()
        if max_val < 0.01:
            max_val = 1.0

        result = []
        for row in self.grid:
            result_row = []
            for value in row:
                # Normalize to [0, 1]
                norm = value / max_val

                # Map to color (cyan to yellow gradient)
                if norm < 0.05:
                    char = ' '
                    fg = (50, 50, 50)
                    bg = (0, 0, 0)
                else:
                    # Gradient: dark blue → cyan → green → yellow
                    if norm < 0.33:
                        # Blue to cyan
                        t = norm / 0.33
                        r = int(t * 50)
                        g = int(t * 150)
                        b = int(150 + t * 50)
                    elif norm < 0.66:
                        # Cyan to green
                        t = (norm - 0.33) / 0.33
                        r = int(50 + t * 50)
                        g = int(150 + t * 105)
                        b = int(200 - t * 200)
                    else:
                        # Green to yellow
                        t = (norm - 0.66) / 0.34
                        r = int(100 + t * 155)
                        g = 255
                        b = 0

                    char = '·' if norm < 0.5 else '∘' if norm < 0.8 else '●'
                    fg = (r, g, b)
                    bg = (0, 0, 0)

                result_row.append((char, fg, bg))
            result.append(result_row)
        return result
