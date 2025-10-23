#!/usr/bin/env python3
"""
walker.py - Base walker entity for terminal automata

Walkers are entities that:
- Move through 2D space
- Carry genetic traits (genome)
- Interact with fields (deposit/sense)
- Reproduce with other walkers
- Age and potentially die

Behavior is injected (not hardcoded) for maximum modularity.
"""

import random
from typing import Optional, Tuple, Any
from dataclasses import dataclass
from src.genetics import Genome


@dataclass
class WalkerState:
    """
    Immutable snapshot of walker state for rendering/metrics.
    Separates state from behavior.
    """
    x: int
    y: int
    char: str
    color_rgb: Tuple[int, int, int]
    genome: Genome
    age: int
    vigor: float


class Walker:
    """
    Base walker entity with position, genetics, and lifecycle.

    Walkers are agents that move through terminal space. They:
    - Have a position (x, y)
    - Carry a genome (color, vigor, traits)
    - Age over time
    - Can reproduce, die, sense, and deposit

    Behavior strategies are injected (not inherited) for composition.
    """

    def __init__(self, x: int, y: int, genome: Optional[Genome] = None,
                 char: str = "·", age: int = 0):
        """
        Initialize walker.

        Args:
            x, y: Initial position
            genome: Genetic traits (creates random if None)
            char: Display character (can be overridden by renderer)
            age: Initial age (typically 0 for newborns)
        """
        self.x = x
        self.y = y
        self.genome = genome or Genome()
        self.char = char
        self.age = age
        self.is_alive = True

        # Derived from genome
        self.vigor = self.genome.vigor

    def move(self, dx: int, dy: int, width: int, height: int, wrap: bool = True):
        """
        Move walker by offset, handling boundaries.

        Args:
            dx, dy: Position offset
            width, height: Grid dimensions
            wrap: If True, wrap around edges; if False, clamp
        """
        if wrap:
            self.x = (self.x + dx) % width
            self.y = (self.y + dy) % height
        else:
            self.x = max(0, min(width - 1, self.x + dx))
            self.y = max(0, min(height - 1, self.y + dy))

    def move_to(self, x: int, y: int, width: int, height: int, wrap: bool = True):
        """
        Move walker to absolute position.

        Args:
            x, y: Target position
            width, height: Grid dimensions
            wrap: If True, wrap coordinates; if False, clamp
        """
        if wrap:
            self.x = x % width
            self.y = y % height
        else:
            self.x = max(0, min(width - 1, x))
            self.y = max(0, min(height - 1, y))

    def reproduce_with(self, other: 'Walker', x: int, y: int,
                      mutation_rate: float = 0.03) -> 'Walker':
        """
        Create offspring walker from two parents.

        Args:
            other: Other parent walker
            x, y: Position for offspring
            mutation_rate: Genome mutation rate

        Returns:
            New Walker instance (child)
        """
        child_genome = self.genome.reproduce_with(other.genome, mutation_rate)
        return Walker(x, y, genome=child_genome, char=self.char, age=0)

    def can_breed_with(self, other: 'Walker', threshold: float = 0.25) -> bool:
        """
        Check if this walker can reproduce with another.
        Uses genome compatibility check.

        Args:
            other: Walker to check breeding compatibility with
            threshold: Maximum genetic distance for breeding

        Returns:
            True if breeding is allowed
        """
        return self.genome.can_breed_with(other.genome, threshold)

    def increment_age(self, amount: int = 1):
        """Increase walker age (call once per tick)"""
        self.age += amount

    def die(self):
        """Mark walker as dead"""
        self.is_alive = False

    def should_die(self, max_age: Optional[int] = None,
                   vigor_threshold: float = 0.1) -> bool:
        """
        Check if walker should die based on age or vigor.

        Args:
            max_age: If set, die when age exceeds this
            vigor_threshold: Die if vigor drops below this

        Returns:
            True if walker should be removed
        """
        if max_age and self.age > max_age:
            return True
        if self.vigor < vigor_threshold:
            return True
        return False

    def modify_vigor(self, delta: float):
        """
        Change vigor level (through competition, resource consumption, etc.)

        Args:
            delta: Amount to add/subtract from vigor
        """
        self.vigor = max(0.0, self.vigor + delta)
        self.genome.vigor = self.vigor  # Keep genome in sync

    def get_state(self) -> WalkerState:
        """
        Get immutable state snapshot for rendering.

        Returns:
            WalkerState with current position, color, and traits
        """
        return WalkerState(
            x=self.x,
            y=self.y,
            char=self.char,
            color_rgb=self.genome.to_rgb(),
            genome=self.genome,
            age=self.age,
            vigor=self.vigor
        )

    def distance_to(self, other: 'Walker') -> float:
        """
        Euclidean distance to another walker.

        Args:
            other: Walker to measure distance to

        Returns:
            Distance in grid units
        """
        return ((self.x - other.x)**2 + (self.y - other.y)**2)**0.5

    def genetic_distance_to(self, other: 'Walker') -> float:
        """
        Genetic distance to another walker.

        Args:
            other: Walker to measure genetic distance to

        Returns:
            Genetic distance [0, 0.5]
        """
        return self.genome.distance_to(other.genome)

    def __repr__(self) -> str:
        return f"Walker(x={self.x}, y={self.y}, age={self.age}, {self.genome})"
