#!/usr/bin/env python3
"""
genome.py - Memetic trait system for terminal automata

Genomes encode inheritable traits:
- color_h: Primary hue [0, 1) - the visible "phenotype"
- vigor: Competitive strength / fitness weight
- traits: Extensible dict for custom properties

Colors flow through populations via reproduction with Gaussian drift.
"""

import random
import math
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


def wrap_hue(h: float) -> float:
    """Wrap hue to [0, 1) range"""
    return h % 1.0


def circular_distance(h1: float, h2: float) -> float:
    """
    Distance between two hues on circular color wheel [0, 1).
    Returns value in [0, 0.5] (max distance is halfway around wheel).
    """
    delta = abs(h1 - h2)
    return min(delta, 1.0 - delta)


def circular_mean(hues: list[float], weights: Optional[list[float]] = None) -> float:
    """
    Weighted circular mean of hues using vector averaging.

    Args:
        hues: List of hue values [0, 1)
        weights: Optional weights (defaults to equal weighting)

    Returns:
        Mean hue in [0, 1)
    """
    if not hues:
        return 0.0

    if weights is None:
        weights = [1.0] * len(hues)

    # Convert to angles and use vector averaging
    cos_sum = sum(w * math.cos(2 * math.pi * h) for h, w in zip(hues, weights))
    sin_sum = sum(w * math.sin(2 * math.pi * h) for h, w in zip(hues, weights))

    mean_angle = math.atan2(sin_sum, cos_sum)
    return wrap_hue(mean_angle / (2 * math.pi))


@dataclass
class Genome:
    """
    Genetic trait container with memetic inheritance.

    Attributes:
        color_h: Hue value [0, 1) - primary visual trait
        vigor: Fitness/dominance weight [0, ∞) - affects inheritance
        saturation: Color saturation [0, 1]
        value: Color brightness [0, 1]
        traits: Extensible dict for custom properties
    """

    color_h: float = field(default_factory=random.random)
    vigor: float = 1.0
    saturation: float = 0.8
    value: float = 0.9
    traits: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Normalize values to valid ranges"""
        self.color_h = wrap_hue(self.color_h)
        self.vigor = max(0.0, self.vigor)
        self.saturation = max(0.0, min(1.0, self.saturation))
        self.value = max(0.0, min(1.0, self.value))

    def reproduce_with(self, other: 'Genome', mutation_rate: float = 0.03) -> 'Genome':
        """
        Create offspring genome by blending with another genome.

        - Hue: Weighted circular mean + Gaussian drift
        - Vigor: Average + small variation
        - Saturation/Value: Average with drift
        - Traits: Blend numeric traits, randomly select others

        Args:
            other: Parent genome to reproduce with
            mutation_rate: Standard deviation of Gaussian drift

        Returns:
            New child genome
        """
        # Weighted circular mean for hue (vigor determines dominance)
        child_h = circular_mean(
            [self.color_h, other.color_h],
            [self.vigor, other.vigor]
        )

        # Add mutation (Gaussian drift)
        child_h = wrap_hue(child_h + random.gauss(0, mutation_rate))

        # Vigor: Average with small random variation
        child_vigor = (self.vigor + other.vigor) / 2
        child_vigor *= random.uniform(0.9, 1.1)

        # Saturation/Value: Blend with drift
        child_sat = (self.saturation + other.saturation) / 2
        child_sat = max(0.0, min(1.0, child_sat + random.gauss(0, mutation_rate)))

        child_val = (self.value + other.value) / 2
        child_val = max(0.0, min(1.0, child_val + random.gauss(0, mutation_rate)))

        # Blend custom traits
        child_traits = {}
        all_keys = set(self.traits.keys()) | set(other.traits.keys())

        for key in all_keys:
            self_val = self.traits.get(key)
            other_val = other.traits.get(key)

            # If both have the trait
            if self_val is not None and other_val is not None:
                # Numeric: average
                if isinstance(self_val, (int, float)) and isinstance(other_val, (int, float)):
                    child_traits[key] = (self_val + other_val) / 2
                # Otherwise: random selection
                else:
                    child_traits[key] = random.choice([self_val, other_val])
            # Only one parent has it: 50% chance of inheritance
            elif random.random() < 0.5:
                child_traits[key] = self_val if self_val is not None else other_val

        return Genome(
            color_h=child_h,
            vigor=child_vigor,
            saturation=child_sat,
            value=child_val,
            traits=child_traits
        )

    def distance_to(self, other: 'Genome') -> float:
        """
        Genetic distance to another genome (for speciation).
        Based on circular hue distance.

        Returns:
            Distance in [0, 0.5]
        """
        return circular_distance(self.color_h, other.color_h)

    def can_breed_with(self, other: 'Genome', threshold: float = 0.25) -> bool:
        """
        Check if genomes are compatible for breeding.
        Implements reproductive barrier based on color distance.

        Args:
            other: Genome to check compatibility with
            threshold: Maximum distance for breeding (0.25 = 90° on color wheel)

        Returns:
            True if breeding is allowed
        """
        return self.distance_to(other) < threshold

    def mutate(self, rate: float = 0.05) -> 'Genome':
        """
        Create mutated copy of this genome.

        Args:
            rate: Mutation strength (stddev for Gaussian noise)

        Returns:
            New mutated genome
        """
        return Genome(
            color_h=wrap_hue(self.color_h + random.gauss(0, rate)),
            vigor=max(0.1, self.vigor * random.uniform(0.8, 1.2)),
            saturation=max(0.0, min(1.0, self.saturation + random.gauss(0, rate))),
            value=max(0.0, min(1.0, self.value + random.gauss(0, rate))),
            traits=self.traits.copy()
        )

    def to_rgb(self) -> tuple[int, int, int]:
        """
        Convert genome color to RGB tuple.

        Returns:
            (r, g, b) values in [0, 255]
        """
        import colorsys
        r, g, b = colorsys.hsv_to_rgb(self.color_h, self.saturation, self.value)
        return (int(r * 255), int(g * 255), int(b * 255))

    def __repr__(self) -> str:
        return f"Genome(h={self.color_h:.3f}, v={self.vigor:.2f})"
