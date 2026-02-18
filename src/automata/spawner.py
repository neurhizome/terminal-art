#!/usr/bin/env python3
"""
spawner.py - Population management for walker experiments

Handles:
- Adding/removing walkers
- Population limits
- Spawning new walkers
- Aging and death
- Spatial querying (neighbors)
"""

import random
from typing import List, Optional, Callable, Tuple
from .walker import Walker
from src.genetics import Genome


class Spawner:
    """
    Manages a population of walkers with lifecycle control.

    Responsibilities:
    - Maintain walker list
    - Enforce population limits
    - Remove dead walkers
    - Spawn new walkers at random or specific positions
    - Find neighbors for interaction
    """

    def __init__(self, max_walkers: int = 500, width: int = 80, height: int = 24):
        """
        Initialize spawner.

        Args:
            max_walkers: Maximum population size
            width, height: Grid dimensions for spawning
        """
        self.walkers: List[Walker] = []
        self.max_walkers = max_walkers
        self.width = width
        self.height = height
        self.total_spawned = 0  # Track total lifetime spawns
        self.total_deaths = 0   # Track total deaths

    def add(self, walker: Walker) -> bool:
        """
        Add walker to population.

        Args:
            walker: Walker instance to add

        Returns:
            True if added, False if population is full
        """
        if len(self.walkers) >= self.max_walkers:
            return False
        self.walkers.append(walker)
        self.total_spawned += 1
        return True

    def spawn_random(self, genome: Optional[Genome] = None, char: str = "·") -> Optional[Walker]:
        """
        Spawn walker at random position.

        Args:
            genome: Genetic traits (creates random if None)
            char: Display character

        Returns:
            New Walker if spawned, None if population full
        """
        if len(self.walkers) >= self.max_walkers:
            return None

        x = random.randint(0, self.width - 1)
        y = random.randint(0, self.height - 1)
        walker = Walker(x, y, genome=genome, char=char)

        if self.add(walker):
            return walker
        return None

    def spawn_at(self, x: int, y: int, genome: Optional[Genome] = None,
                 char: str = "·") -> Optional[Walker]:
        """
        Spawn walker at specific position.

        Args:
            x, y: Position
            genome: Genetic traits (creates random if None)
            char: Display character

        Returns:
            New Walker if spawned, None if population full
        """
        if len(self.walkers) >= self.max_walkers:
            return None

        walker = Walker(x, y, genome=genome, char=char)
        if self.add(walker):
            return walker
        return None

    def spawn_from_parents(self, parent1: Walker, parent2: Walker,
                          x: Optional[int] = None, y: Optional[int] = None,
                          mutation_rate: float = 0.03) -> Optional[Walker]:
        """
        Spawn offspring from two parent walkers.

        Args:
            parent1, parent2: Parent walkers
            x, y: Position (if None, use midpoint between parents)
            mutation_rate: Genome mutation rate

        Returns:
            New Walker if spawned, None if population full or incompatible parents
        """
        if not parent1.can_breed_with(parent2):
            return None

        if len(self.walkers) >= self.max_walkers:
            return None

        # Default to midpoint between parents
        if x is None:
            x = (parent1.x + parent2.x) // 2
        if y is None:
            y = (parent1.y + parent2.y) // 2

        child = parent1.reproduce_with(parent2, x, y, mutation_rate)
        if self.add(child):
            return child
        return None

    def remove_dead(self, max_age: Optional[int] = None,
                   vigor_threshold: float = 0.1) -> int:
        """
        Remove walkers that should die.

        Args:
            max_age: If set, die when age exceeds this
            vigor_threshold: Die if vigor drops below this

        Returns:
            Number of walkers removed
        """
        initial_count = len(self.walkers)

        self.walkers = [
            w for w in self.walkers
            if not w.should_die(max_age, vigor_threshold)
        ]

        removed = initial_count - len(self.walkers)
        self.total_deaths += removed
        return removed

    def age_all(self, amount: int = 1):
        """
        Increment age for all walkers.

        Args:
            amount: Age increment per call
        """
        for walker in self.walkers:
            walker.increment_age(amount)

    def find_neighbors(self, walker: Walker, radius: float) -> List[Walker]:
        """
        Find walkers within radius of given walker.

        Args:
            walker: Center walker
            radius: Search radius

        Returns:
            List of walkers within radius (excluding center walker)
        """
        neighbors = []
        for other in self.walkers:
            if other is walker:
                continue
            if walker.distance_to(other) <= radius:
                neighbors.append(other)
        return neighbors

    def find_breeding_partners(self, walker: Walker, radius: float,
                             threshold: float = 0.25) -> List[Walker]:
        """
        Find compatible breeding partners near walker.

        Args:
            walker: Walker looking for mate
            radius: Search radius
            threshold: Maximum genetic distance for breeding

        Returns:
            List of compatible walkers within radius
        """
        neighbors = self.find_neighbors(walker, radius)
        return [
            other for other in neighbors
            if walker.can_breed_with(other, threshold)
        ]

    def clear(self):
        """Remove all walkers"""
        self.walkers.clear()

    def count(self) -> int:
        """Get current population size"""
        return len(self.walkers)

    def is_full(self) -> bool:
        """Check if population is at capacity"""
        return len(self.walkers) >= self.max_walkers

    def get_stats(self) -> dict:
        """
        Get population statistics.

        Returns:
            Dict with current count, total spawned, total deaths, avg age, avg vigor
        """
        if not self.walkers:
            return {
                'count': 0,
                'total_spawned': self.total_spawned,
                'total_deaths': self.total_deaths,
                'avg_age': 0,
                'avg_vigor': 0,
            }

        avg_age = sum(w.age for w in self.walkers) / len(self.walkers)
        avg_vigor = sum(w.vigor for w in self.walkers) / len(self.walkers)

        return {
            'count': len(self.walkers),
            'total_spawned': self.total_spawned,
            'total_deaths': self.total_deaths,
            'avg_age': avg_age,
            'avg_vigor': avg_vigor,
        }

    def __len__(self) -> int:
        return len(self.walkers)

    def __iter__(self):
        return iter(self.walkers)
