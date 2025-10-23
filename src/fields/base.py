#!/usr/bin/env python3
"""
base.py - Abstract field interface for grid-based systems

Fields are 2D grids that store and update values.
Different field types implement different dynamics:
- Diffusion (spreading and decay)
- Territory (ownership tracking)
- Energy (excitable medium)
- Connection (NESW bitmasks)

All fields share common interface for get/set/update/render.
"""

from abc import ABC, abstractmethod
from typing import Tuple, Optional, Any, List


class Field(ABC):
    """
    Abstract base for 2D grid-based systems.

    Fields maintain state in a grid and update according to specific rules.
    They can be sensed by walkers and modified through deposits.
    """

    def __init__(self, width: int, height: int):
        """
        Initialize field.

        Args:
            width, height: Grid dimensions
        """
        self.width = width
        self.height = height

    @abstractmethod
    def get(self, x: int, y: int) -> Any:
        """
        Read value at position.

        Args:
            x, y: Grid coordinates

        Returns:
            Value at (x, y)
        """
        pass

    @abstractmethod
    def set(self, x: int, y: int, value: Any):
        """
        Write value at position.

        Args:
            x, y: Grid coordinates
            value: Value to write
        """
        pass

    @abstractmethod
    def update(self):
        """
        Apply field dynamics (diffusion, decay, etc.).
        Called once per simulation tick.
        """
        pass

    @abstractmethod
    def render(self) -> List[List[Tuple[str, Tuple[int, int, int], Tuple[int, int, int]]]]:
        """
        Convert field to renderable grid.

        Returns:
            2D list of (char, fg_color, bg_color) tuples
            Colors are (r, g, b) in [0, 255]
        """
        pass

    def clear(self):
        """Reset field to initial state"""
        pass

    def in_bounds(self, x: int, y: int) -> bool:
        """
        Check if coordinates are within bounds.

        Args:
            x, y: Coordinates to check

        Returns:
            True if in bounds
        """
        return 0 <= x < self.width and 0 <= y < self.height

    def wrap(self, x: int, y: int) -> Tuple[int, int]:
        """
        Wrap coordinates to grid (toroidal topology).

        Args:
            x, y: Coordinates to wrap

        Returns:
            (x, y) wrapped to [0, width) x [0, height)
        """
        return (x % self.width, y % self.height)

    def clamp(self, x: int, y: int) -> Tuple[int, int]:
        """
        Clamp coordinates to grid bounds.

        Args:
            x, y: Coordinates to clamp

        Returns:
            (x, y) clamped to valid range
        """
        x = max(0, min(self.width - 1, x))
        y = max(0, min(self.height - 1, y))
        return (x, y)


class ScalarField(Field):
    """
    Field that stores single numeric value per cell.

    Base class for diffusion, energy, and other continuous fields.
    """

    def __init__(self, width: int, height: int, initial_value: float = 0.0):
        """
        Initialize scalar field.

        Args:
            width, height: Grid dimensions
            initial_value: Default value for all cells
        """
        super().__init__(width, height)
        self.grid = [[initial_value for _ in range(width)] for _ in range(height)]

    def get(self, x: int, y: int) -> float:
        """Get scalar value at position"""
        if not self.in_bounds(x, y):
            return 0.0
        return self.grid[y][x]

    def set(self, x: int, y: int, value: float):
        """Set scalar value at position"""
        if self.in_bounds(x, y):
            self.grid[y][x] = value

    def add(self, x: int, y: int, delta: float):
        """Add value to cell (deposit)"""
        if self.in_bounds(x, y):
            self.grid[y][x] += delta

    def max_value(self) -> float:
        """Get maximum value in field"""
        return max(max(row) for row in self.grid)

    def min_value(self) -> float:
        """Get minimum value in field"""
        return min(min(row) for row in self.grid)

    def sum_value(self) -> float:
        """Get total field value"""
        return sum(sum(row) for row in self.grid)

    def clear(self):
        """Reset all values to 0"""
        self.grid = [[0.0 for _ in range(self.width)] for _ in range(self.height)]

    def update(self):
        """Default: no dynamics (override in subclasses)"""
        pass

    def render(self) -> List[List[Tuple[str, Tuple[int, int, int], Tuple[int, int, int]]]]:
        """
        Default: render as intensity gradient (grayscale).
        Override for custom visualization.
        """
        max_val = self.max_value()
        if max_val == 0:
            max_val = 1.0

        result = []
        for row in self.grid:
            result_row = []
            for value in row:
                intensity = int((value / max_val) * 255)
                intensity = max(0, min(255, intensity))
                char = ' ' if intensity < 30 else '·'
                fg = (intensity, intensity, intensity)
                bg = (0, 0, 0)
                result_row.append((char, fg, bg))
            result.append(result_row)
        return result


class DiscreteField(Field):
    """
    Field that stores discrete values (not continuous).

    Base class for territory, connection, and categorical fields.
    """

    def __init__(self, width: int, height: int, initial_value: Any = None):
        """
        Initialize discrete field.

        Args:
            width, height: Grid dimensions
            initial_value: Default value for all cells
        """
        super().__init__(width, height)
        self.grid = [[initial_value for _ in range(width)] for _ in range(height)]

    def get(self, x: int, y: int) -> Any:
        """Get value at position"""
        if not self.in_bounds(x, y):
            return None
        return self.grid[y][x]

    def set(self, x: int, y: int, value: Any):
        """Set value at position"""
        if self.in_bounds(x, y):
            self.grid[y][x] = value

    def clear(self):
        """Reset all values to None"""
        self.grid = [[None for _ in range(self.width)] for _ in range(self.height)]

    def update(self):
        """Default: no dynamics"""
        pass

    def render(self) -> List[List[Tuple[str, Tuple[int, int, int], Tuple[int, int, int]]]]:
        """Default: return empty grid"""
        return [
            [(' ', (128, 128, 128), (0, 0, 0)) for _ in range(self.width)]
            for _ in range(self.height)
        ]
