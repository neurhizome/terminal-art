"""
genetics - Memetic trait system for terminal automata

Provides genome representation, inheritance, and speciation mechanics.
Colors are genetic markers that flow through populations.
"""

from .genome import Genome, circular_mean, circular_distance, wrap_hue
from .quaternion_genome import QuaternionGenome

__all__ = [
    'Genome',
    'QuaternionGenome',
    'circular_mean',
    'circular_distance',
    'wrap_hue',
]
