#!/usr/bin/env python3
"""
event.py - Base event system for perturbative dynamics

Events modulate system parameters over time.
They create temporal variation that drives emergent patterns.

Examples:
- Spawn rate bursts
- Global color shifts
- Vigor modulation waves
- Extinction events
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class Event(ABC):
    """
    Abstract base for temporal perturbations.

    Events have a duration and modify system state during their lifetime.
    """

    def __init__(self, duration: int, name: str = "Event"):
        """
        Initialize event.

        Args:
            duration: How many ticks this event lasts
            name: Human-readable event name
        """
        self.duration = duration
        self.name = name
        self.elapsed = 0
        self.active = True

    @abstractmethod
    def apply(self, system: Dict[str, Any]):
        """
        Modify system state.

        Args:
            system: Dict containing system parameters and objects
                   (spawner, fields, config, etc.)
        """
        pass

    def update(self):
        """
        Advance event timer.
        Called once per tick.
        """
        self.elapsed += 1
        if self.elapsed >= self.duration:
            self.active = False

    def is_finished(self) -> bool:
        """Check if event has completed"""
        return not self.active

    def progress(self) -> float:
        """
        Get event progress [0, 1].

        Returns:
            Fraction of duration elapsed
        """
        return min(1.0, self.elapsed / self.duration)

    def __repr__(self) -> str:
        return f"{self.name} ({self.elapsed}/{self.duration})"


class SpawnRateBurst(Event):
    """
    Temporarily increase spawning rate.

    Creates population surges that compete for resources.
    """

    def __init__(self, duration: int, multiplier: float = 2.0):
        """
        Args:
            duration: Event duration in ticks
            multiplier: Spawn rate multiplier (2.0 = double rate)
        """
        super().__init__(duration, name="Spawn Burst")
        self.multiplier = multiplier

    def apply(self, system: Dict[str, Any]):
        """
        Increase spawn rate in system config.

        Expects system['config']['spawn_rate'] to exist.
        """
        if 'config' in system and 'spawn_rate' in system['config']:
            system['config']['spawn_rate'] *= self.multiplier


class GlobalColorShift(Event):
    """
    Rotate all walker hues by constant amount.

    Creates synchronized color waves across population.
    """

    def __init__(self, duration: int, shift_rate: float = 0.01):
        """
        Args:
            duration: Event duration in ticks
            shift_rate: Hue shift per tick [0, 1)
        """
        super().__init__(duration, name="Color Shift")
        self.shift_rate = shift_rate

    def apply(self, system: Dict[str, Any]):
        """
        Shift all walker hues.

        Expects system['spawner'] to exist.
        """
        if 'spawner' not in system:
            return

        spawner = system['spawner']
        for walker in spawner.walkers:
            walker.genome.color_h = (walker.genome.color_h + self.shift_rate) % 1.0


class VigorWave(Event):
    """
    Modulate walker vigor with sinusoidal wave.

    Creates oscillating competitive dynamics.
    """

    def __init__(self, duration: int, amplitude: float = 0.3):
        """
        Args:
            duration: Event duration in ticks
            amplitude: Wave amplitude
        """
        super().__init__(duration, name="Vigor Wave")
        self.amplitude = amplitude

    def apply(self, system: Dict[str, Any]):
        """
        Apply sinusoidal vigor modulation.

        Expects system['spawner'] to exist.
        """
        import math

        if 'spawner' not in system:
            return

        # Sinusoidal modulation
        phase = (self.elapsed / self.duration) * 2 * math.pi
        modifier = math.sin(phase) * self.amplitude

        spawner = system['spawner']
        for walker in spawner.walkers:
            walker.modify_vigor(modifier)


class ExtinctionEvent(Event):
    """
    Remove weakest walkers (low vigor).

    Creates selection pressure.
    """

    def __init__(self, duration: int, threshold: float = 0.5):
        """
        Args:
            duration: Event duration (kills happen at start)
            threshold: Walkers with vigor < this are removed
        """
        super().__init__(duration, name="Extinction")
        self.threshold = threshold
        self.triggered = False

    def apply(self, system: Dict[str, Any]):
        """
        Remove low-vigor walkers.

        Expects system['spawner'] to exist.
        """
        if self.triggered:
            return

        if 'spawner' not in system:
            return

        spawner = system['spawner']
        initial_count = len(spawner.walkers)

        # Remove low-vigor walkers
        spawner.walkers = [
            w for w in spawner.walkers
            if w.vigor >= self.threshold
        ]

        removed = initial_count - len(spawner.walkers)
        spawner.total_deaths += removed

        self.triggered = True


class MutationStorm(Event):
    """
    Increase mutation rate temporarily.

    Injects genetic diversity.
    """

    def __init__(self, duration: int, rate_multiplier: float = 3.0):
        """
        Args:
            duration: Event duration in ticks
            rate_multiplier: Mutation rate multiplier
        """
        super().__init__(duration, name="Mutation Storm")
        self.rate_multiplier = rate_multiplier

    def apply(self, system: Dict[str, Any]):
        """
        Increase mutation rate in config.

        Expects system['config']['mutation_rate'] to exist.
        """
        if 'config' in system and 'mutation_rate' in system['config']:
            system['config']['mutation_rate'] *= self.rate_multiplier


class ResourceDepletion(Event):
    """
    Reduce vigor of all walkers.

    Simulates resource scarcity.
    """

    def __init__(self, duration: int, depletion_rate: float = 0.01):
        """
        Args:
            duration: Event duration in ticks
            depletion_rate: Vigor loss per tick
        """
        super().__init__(duration, name="Resource Depletion")
        self.depletion_rate = depletion_rate

    def apply(self, system: Dict[str, Any]):
        """
        Reduce vigor for all walkers.

        Expects system['spawner'] to exist.
        """
        if 'spawner' not in system:
            return

        spawner = system['spawner']
        for walker in spawner.walkers:
            walker.modify_vigor(-self.depletion_rate)


class EqualTemperament(Event):
    """
    Snap all walker hues to the 12-tone equal-tempered chromatic scale.

    Each color_h is rounded to the nearest k/12 (k ∈ 0..11).  After the
    snap, every inter-walker hue interval is exactly 7/12 ≈ 0.58333 —
    slightly flat of the Pythagorean fifth (log2(1.5) ≈ 0.58496).

    The consequence: the Pythagorean comma drift that had been slowly
    accumulating is wiped to zero and immediately restarts from a clean
    baseline. The second cycle of drift becomes visible as a measurable
    hue shift relative to the snapped positions — the comma that cannot
    be made to vanish, only momentarily hidden.
    """

    def __init__(self, duration: int = 80):
        """
        Args:
            duration: Event duration in ticks (snap happens on first tick)
        """
        super().__init__(duration, name="Equal Temperament")
        self.triggered = False

    def apply(self, system: Dict[str, Any]):
        """
        Snap all hues to nearest semitone.

        Expects system['spawner'] to exist.
        """
        if self.triggered:
            return

        if 'spawner' not in system:
            return

        for walker in system['spawner'].walkers:
            k = round(walker.genome.color_h * 12) % 12
            walker.genome.color_h = k / 12.0

        self.triggered = True


class FieldPulse(Event):
    """
    Add energy burst to diffusion field.

    Creates localized perturbation.
    """

    def __init__(self, duration: int, x: int, y: int, strength: float = 10.0):
        """
        Args:
            duration: Event duration (pulse happens at start)
            x, y: Pulse center
            strength: Energy added
        """
        super().__init__(duration, name="Field Pulse")
        self.x = x
        self.y = y
        self.strength = strength
        self.triggered = False

    def apply(self, system: Dict[str, Any]):
        """
        Deposit energy to field.

        Expects system['field'] (DiffusionField) to exist.
        """
        if self.triggered:
            return

        if 'field' not in system:
            return

        field = system['field']
        field.deposit(self.x, self.y, self.strength)

        self.triggered = True
