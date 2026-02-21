"""
events - Perturbative dynamics for temporal variation

Provides event system for modulating system parameters over time.
Events create the temporal "heartbeat" that drives emergent patterns.
"""

from .event import (
    Event,
    SpawnRateBurst,
    GlobalColorShift,
    VigorWave,
    ExtinctionEvent,
    MutationStorm,
    ResourceDepletion,
    FieldPulse,
    EqualTemperament,
)
from .scheduler import EventScheduler, PeriodicEventSpawner
from .catalog import (
    CHAOS_POOL,
    AESTHETIC_POOL,
    COMPETITIVE_POOL,
    GENTLE_POOL,
    ALL_EVENTS_POOL,
)

__all__ = [
    'Event',
    'SpawnRateBurst',
    'GlobalColorShift',
    'VigorWave',
    'ExtinctionEvent',
    'MutationStorm',
    'ResourceDepletion',
    'FieldPulse',
    'EqualTemperament',
    'EventScheduler',
    'PeriodicEventSpawner',
    'CHAOS_POOL',
    'AESTHETIC_POOL',
    'COMPETITIVE_POOL',
    'GENTLE_POOL',
    'ALL_EVENTS_POOL',
]
