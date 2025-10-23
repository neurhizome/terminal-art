#!/usr/bin/env python3
"""
scheduler.py - Event timing and triggering system

Manages event lifecycle:
- Scheduling future events
- Triggering active events
- Removing finished events
- Random event spawning
"""

import random
from typing import List, Dict, Any, Callable, Optional
from .event import Event


class EventScheduler:
    """
    Manages temporal event system.

    Schedules, triggers, and removes events over time.
    """

    def __init__(self):
        """Initialize empty scheduler"""
        self.active_events: List[Event] = []
        self.scheduled_events: List[tuple[int, Event]] = []  # (trigger_tick, event)
        self.current_tick = 0

    def add_event(self, event: Event, delay: int = 0):
        """
        Schedule event to start after delay.

        Args:
            event: Event instance to schedule
            delay: Ticks to wait before starting (0 = immediate)
        """
        if delay == 0:
            self.active_events.append(event)
        else:
            trigger_tick = self.current_tick + delay
            self.scheduled_events.append((trigger_tick, event))

    def update(self, system: Dict[str, Any]):
        """
        Update all active events and trigger scheduled ones.

        Args:
            system: System state dict passed to events
        """
        self.current_tick += 1

        # Trigger scheduled events
        to_activate = []
        remaining = []

        for trigger_tick, event in self.scheduled_events:
            if trigger_tick <= self.current_tick:
                to_activate.append(event)
            else:
                remaining.append((trigger_tick, event))

        self.scheduled_events = remaining
        self.active_events.extend(to_activate)

        # Update and apply active events
        finished = []

        for event in self.active_events:
            event.apply(system)
            event.update()

            if event.is_finished():
                finished.append(event)

        # Remove finished events
        for event in finished:
            self.active_events.remove(event)

    def spawn_random_event(self, event_pool: List[Callable[[], Event]],
                          delay_range: tuple[int, int] = (0, 100)):
        """
        Schedule random event from pool.

        Args:
            event_pool: List of event factory functions
            delay_range: (min, max) delay before triggering
        """
        if not event_pool:
            return

        event_factory = random.choice(event_pool)
        event = event_factory()
        delay = random.randint(*delay_range)

        self.add_event(event, delay)

    def clear(self):
        """Remove all events"""
        self.active_events.clear()
        self.scheduled_events.clear()

    def get_active_events(self) -> List[Event]:
        """Get list of currently active events"""
        return self.active_events.copy()

    def get_scheduled_count(self) -> int:
        """Get number of scheduled (not yet active) events"""
        return len(self.scheduled_events)

    def has_active_events(self) -> bool:
        """Check if any events are currently active"""
        return len(self.active_events) > 0

    def get_status_line(self) -> str:
        """
        Get human-readable status string.

        Returns:
            String like "Active: Spawn Burst (50/100) | Scheduled: 2"
        """
        if not self.active_events and not self.scheduled_events:
            return "No events"

        parts = []

        if self.active_events:
            event_names = [str(e) for e in self.active_events]
            parts.append(f"Active: {', '.join(event_names)}")

        if self.scheduled_events:
            parts.append(f"Scheduled: {len(self.scheduled_events)}")

        return " | ".join(parts)


class PeriodicEventSpawner:
    """
    Automatically spawn random events at regular intervals.

    Useful for continuous perturbation experiments.
    """

    def __init__(self, scheduler: EventScheduler,
                 event_pool: List[Callable[[], Event]],
                 interval_range: tuple[int, int] = (100, 300)):
        """
        Initialize periodic spawner.

        Args:
            scheduler: EventScheduler to add events to
            event_pool: List of event factory functions
            interval_range: (min, max) ticks between spawns
        """
        self.scheduler = scheduler
        self.event_pool = event_pool
        self.interval_range = interval_range
        self.ticks_until_next = random.randint(*interval_range)

    def update(self):
        """
        Check if it's time to spawn new event.
        Call once per tick.
        """
        self.ticks_until_next -= 1

        if self.ticks_until_next <= 0:
            # Spawn event
            self.scheduler.spawn_random_event(self.event_pool, delay_range=(0, 50))

            # Schedule next spawn
            self.ticks_until_next = random.randint(*self.interval_range)
