#!/usr/bin/env python3
"""
catalog.py - Pre-built event library

Collection of ready-to-use event factory functions.
Use with EventScheduler.spawn_random_event() or PeriodicEventSpawner.
"""

import random
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


def make_spawn_burst() -> Event:
    """Factory: Spawn rate burst"""
    return SpawnRateBurst(
        duration=random.randint(50, 150),
        multiplier=random.uniform(1.5, 3.0)
    )


def make_color_shift() -> Event:
    """Factory: Global color rotation"""
    return GlobalColorShift(
        duration=random.randint(100, 300),
        shift_rate=random.uniform(0.005, 0.02)
    )


def make_vigor_wave() -> Event:
    """Factory: Sinusoidal vigor modulation"""
    return VigorWave(
        duration=random.randint(80, 200),
        amplitude=random.uniform(0.2, 0.5)
    )


def make_extinction() -> Event:
    """Factory: Remove weak walkers"""
    return ExtinctionEvent(
        duration=50,
        threshold=random.uniform(0.3, 0.6)
    )


def make_mutation_storm() -> Event:
    """Factory: Increase mutation rate"""
    return MutationStorm(
        duration=random.randint(50, 100),
        rate_multiplier=random.uniform(2.0, 5.0)
    )


def make_resource_depletion() -> Event:
    """Factory: Gradual vigor loss"""
    return ResourceDepletion(
        duration=random.randint(100, 200),
        depletion_rate=random.uniform(0.005, 0.02)
    )


def make_field_pulse(width: int, height: int) -> Event:
    """
    Factory: Localized field energy burst

    Args:
        width, height: Grid dimensions for random positioning
    """
    return FieldPulse(
        duration=20,
        x=random.randint(0, width - 1),
        y=random.randint(0, height - 1),
        strength=random.uniform(5.0, 15.0)
    )


def make_equal_temperament() -> Event:
    """Factory: Snap all hues to 12-TET chromatic grid"""
    return EqualTemperament(duration=80)


# Pre-defined event pools for different experiment types

CHAOS_POOL = [
    make_spawn_burst,
    make_extinction,
    make_mutation_storm,
    make_resource_depletion,
]
"""High-variance events for chaotic dynamics"""

AESTHETIC_POOL = [
    make_color_shift,
    make_vigor_wave,
    make_spawn_burst,
]
"""Visual events that create beautiful patterns"""

COMPETITIVE_POOL = [
    make_extinction,
    make_resource_depletion,
    make_spawn_burst,
]
"""Selection pressure events"""

GENTLE_POOL = [
    make_color_shift,
    make_vigor_wave,
]
"""Low-impact events for stable systems"""

ALL_EVENTS_POOL = [
    make_spawn_burst,
    make_color_shift,
    make_vigor_wave,
    make_extinction,
    make_mutation_storm,
    make_resource_depletion,
]
"""Complete event catalog"""
