"""
genetics - Memetic trait system for terminal automata

Provides genome representation, inheritance, and speciation mechanics.
Colors are genetic markers that flow through populations.
"""

from .genome import Genome, circular_mean, circular_distance, wrap_hue

__all__ = [
    'Genome',
    'circular_mean',
    'circular_distance',
    'wrap_hue',
]
