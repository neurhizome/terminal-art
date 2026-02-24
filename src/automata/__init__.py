"""
automata - Walker entities and population management

Provides base Walker class, Spawner for population control,
and pluggable Behavior strategies for movement.
"""

from .walker import Walker, WalkerState
from .spawner import Spawner
from .behaviors import (
    MovementBehavior,
    RandomWalk,
    BiasedWalk,
    LevyFlight,
    GradientFollow,
    FifthSeek,
    Stationary,
    Orbit,
    AvoidEdges,
    RecamanWalk,
    LissajousOrbit,
)

__all__ = [
    'Walker',
    'WalkerState',
    'Spawner',
    'MovementBehavior',
    'RandomWalk',
    'BiasedWalk',
    'LevyFlight',
    'GradientFollow',
    'FifthSeek',
    'Stationary',
    'Orbit',
    'AvoidEdges',
    'RecamanWalk',
    'LissajousOrbit',
]
