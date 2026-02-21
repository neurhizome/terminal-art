#!/usr/bin/env python3
"""
behaviors.py - Movement and action strategies for walkers

Behaviors are injected into walkers (not inherited).
This enables hot-swapping strategies and composition.

Common patterns:
- RandomWalk: Unbiased random motion
- BiasedWalk: Directional preference
- LevyFlight: Heavy-tailed step distribution
- Chemotaxis: Follow gradient
- Avoidance: Repel from stimuli
"""

import random
import math
from typing import Tuple, Optional, Protocol
from abc import ABC, abstractmethod


class MovementBehavior(ABC):
    """
    Abstract base for movement strategies.

    Behaviors return (dx, dy) offsets for walker movement.
    They don't modify walker state directly.
    """

    @abstractmethod
    def get_move(self, x: int, y: int, **context) -> Tuple[int, int]:
        """
        Calculate movement offset.

        Args:
            x, y: Current position
            **context: Additional info (field values, neighbors, etc.)

        Returns:
            (dx, dy) offset
        """
        pass


class RandomWalk(MovementBehavior):
    """
    Unbiased random walk (4-way or 8-way).

    Classic random walk - equal probability in all directions.
    """

    def __init__(self, eight_way: bool = False):
        """
        Args:
            eight_way: If True, use 8 directions (includes diagonals)
        """
        self.eight_way = eight_way

        if eight_way:
            self.directions = [
                (0, -1),  (1, -1),  (1, 0),  (1, 1),  # N, NE, E, SE
                (0, 1),   (-1, 1),  (-1, 0), (-1, -1) # S, SW, W, NW
            ]
        else:
            self.directions = [
                (0, -1),  # N
                (1, 0),   # E
                (0, 1),   # S
                (-1, 0),  # W
            ]

    def get_move(self, x: int, y: int, **context) -> Tuple[int, int]:
        return random.choice(self.directions)


class BiasedWalk(MovementBehavior):
    """
    Random walk with directional bias.

    Moves are random but weighted toward a preferred direction.
    """

    def __init__(self, bias_direction: Tuple[int, int] = (1, 0),
                 bias_strength: float = 0.5):
        """
        Args:
            bias_direction: Preferred direction vector (will be normalized)
            bias_strength: How strongly to bias [0=random, 1=always bias]
        """
        self.bias_direction = bias_direction
        self.bias_strength = max(0.0, min(1.0, bias_strength))
        self.random_walk = RandomWalk(eight_way=True)

    def get_move(self, x: int, y: int, **context) -> Tuple[int, int]:
        if random.random() < self.bias_strength:
            # Move in bias direction
            return self.bias_direction
        else:
            # Random move
            return self.random_walk.get_move(x, y)


class LevyFlight(MovementBehavior):
    """
    Lévy flight - rare long jumps with frequent short steps.

    Heavy-tailed step distribution for efficient spatial exploration.
    """

    def __init__(self, alpha: float = 1.5, scale: float = 1.0):
        """
        Args:
            alpha: Lévy exponent (1 < alpha < 3, typical ~1.5)
            scale: Scale parameter for step size
        """
        self.alpha = alpha
        self.scale = scale

    def _levy_step(self) -> float:
        """Generate Lévy-distributed step size"""
        # Using Mantegna's algorithm
        sigma_u = (
            math.gamma(1 + self.alpha) * math.sin(math.pi * self.alpha / 2) /
            (math.gamma((1 + self.alpha) / 2) * self.alpha * (2 ** ((self.alpha - 1) / 2)))
        ) ** (1 / self.alpha)

        u = random.gauss(0, sigma_u)
        v = random.gauss(0, 1)

        step = u / abs(v) ** (1 / self.alpha)
        return step * self.scale

    def get_move(self, x: int, y: int, **context) -> Tuple[int, int]:
        # Random direction
        angle = random.uniform(0, 2 * math.pi)

        # Lévy-distributed step size
        step = self._levy_step()

        dx = int(step * math.cos(angle))
        dy = int(step * math.sin(angle))

        # Clamp to reasonable range
        dx = max(-5, min(5, dx))
        dy = max(-5, min(5, dy))

        return (dx, dy)


class GradientFollow(MovementBehavior):
    """
    Chemotaxis - follow gradient of field values.

    Moves toward increasing (or decreasing) field values.
    """

    def __init__(self, field_name: str = 'scent', attraction: bool = True,
                 sensitivity: float = 1.0):
        """
        Args:
            field_name: Which field to sense (passed in context)
            attraction: If True, move toward higher values; False = repulsion
            sensitivity: How strongly to respond to gradient
        """
        self.field_name = field_name
        self.attraction = attraction
        self.sensitivity = sensitivity

    def get_move(self, x: int, y: int, **context) -> Tuple[int, int]:
        """
        Context should include:
            field: Field object with get(x, y) method
        """
        field = context.get('field')
        if field is None:
            # Fallback to random walk
            return random.choice([(0, -1), (1, 0), (0, 1), (-1, 0)])

        # Sample 4-neighborhood
        current_value = field.get(x, y)
        neighbors = [
            ((0, -1), field.get(x, y - 1)),  # N
            ((1, 0),  field.get(x + 1, y)),  # E
            ((0, 1),  field.get(x, y + 1)),  # S
            ((-1, 0), field.get(x - 1, y)),  # W
        ]

        # Calculate probabilities based on gradient
        if self.attraction:
            # Prefer higher values
            weights = [max(0, val - current_value) for _, val in neighbors]
        else:
            # Prefer lower values
            weights = [max(0, current_value - val) for _, val in neighbors]

        # Apply sensitivity
        weights = [w ** self.sensitivity for w in weights]

        # Normalize to probabilities
        total = sum(weights)
        if total > 0:
            weights = [w / total for w in weights]
            # Weighted random choice
            direction = random.choices([d for d, _ in neighbors], weights=weights)[0]
            return direction
        else:
            # No gradient, random walk
            return random.choice([d for d, _ in neighbors])


class Stationary(MovementBehavior):
    """
    No movement - walker stays in place.

    Useful for fixed obstacles or stationary depositors.
    """

    def get_move(self, x: int, y: int, **context) -> Tuple[int, int]:
        return (0, 0)


class Orbit(MovementBehavior):
    """
    Circular motion around a center point.

    Useful for creating vortex patterns.
    """

    def __init__(self, center_x: int, center_y: int, clockwise: bool = True):
        """
        Args:
            center_x, center_y: Center of orbit
            clockwise: Direction of rotation
        """
        self.center_x = center_x
        self.center_y = center_y
        self.clockwise = clockwise

    def get_move(self, x: int, y: int, **context) -> Tuple[int, int]:
        # Vector from center to current position
        dx = x - self.center_x
        dy = y - self.center_y

        # Rotate 90° (tangent to radius)
        if self.clockwise:
            return (dy, -dx) if (dx != 0 or dy != 0) else (1, 0)
        else:
            return (-dy, dx) if (dx != 0 or dy != 0) else (-1, 0)


class FifthSeek(MovementBehavior):
    """
    Move one step toward a pre-identified spatial target.

    Used in conjunction with the Pythagorean comma experiment: the caller
    finds the nearest 'fifth partner' (a walker whose hue is approximately
    one Pythagorean fifth above self), then passes that partner's position
    via context so this behavior moves the walker toward it.

    If no target is provided, falls back to a random 8-way step.
    """

    def __init__(self):
        self._random = RandomWalk(eight_way=True)

    def get_move(self, x: int, y: int, **context) -> Tuple[int, int]:
        """
        Context kwargs:
            target_x (int): X position of fifth partner
            target_y (int): Y position of fifth partner
        """
        target_x = context.get('target_x')
        target_y = context.get('target_y')

        if target_x is None or target_y is None:
            return self._random.get_move(x, y)

        dx = 0 if target_x == x else (1 if target_x > x else -1)
        dy = 0 if target_y == y else (1 if target_y > y else -1)
        return (dx, dy)


class AvoidEdges(MovementBehavior):
    """
    Bias away from grid boundaries.

    Useful when wrapping is disabled.
    """

    def __init__(self, width: int, height: int, margin: int = 5):
        """
        Args:
            width, height: Grid dimensions
            margin: How close to edge before repulsion kicks in
        """
        self.width = width
        self.height = height
        self.margin = margin
        self.random_walk = RandomWalk(eight_way=True)

    def get_move(self, x: int, y: int, **context) -> Tuple[int, int]:
        dx, dy = 0, 0

        # Repel from edges
        if x < self.margin:
            dx = 1
        elif x > self.width - self.margin:
            dx = -1

        if y < self.margin:
            dy = 1
        elif y > self.height - self.margin:
            dy = -1

        if dx != 0 or dy != 0:
            return (dx, dy)
        else:
            # Not near edge, random walk
            return self.random_walk.get_move(x, y)
