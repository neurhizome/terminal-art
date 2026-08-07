#!/usr/bin/env python3
"""JSONL event parsing for stream-based terminal sketches.

The stream format is intentionally generic and public-safe. Events describe
abstract activity, not private infrastructure:

    {"source": "moth", "kind": "message", "room": "north", "intensity": 0.8}

Coordinates are optional. When omitted, the renderer derives stable positions
from source and room names.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Optional


@dataclass(frozen=True)
class StreamEvent:
    """One activity pulse in a generic event stream."""

    source: str
    kind: str = "event"
    room: str = "field"
    intensity: float = 1.0
    x: Optional[float] = None
    y: Optional[float] = None
    label: str = ""
    t: int = 0

    @classmethod
    def from_dict(cls, raw: dict, index: int = 0) -> "StreamEvent":
        source = str(raw.get("source") or raw.get("sender") or "unknown")
        kind = str(raw.get("kind") or raw.get("type") or "event")
        room = str(raw.get("room") or "field")
        label = str(raw.get("label") or raw.get("content") or "")
        return cls(
            source=source,
            kind=kind,
            room=room,
            intensity=_clamp(float(raw.get("intensity", 1.0)), 0.0, 3.0),
            x=_optional_float(raw.get("x")),
            y=_optional_float(raw.get("y")),
            label=label,
            t=int(raw.get("t", raw.get("tick", index))),
        )


def _optional_float(value: object) -> Optional[float]:
    if value is None:
        return None
    return float(value)


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def iter_events(path: Path) -> Iterator[StreamEvent]:
    """Yield events from a JSONL file, skipping blank lines and comments."""
    with path.open(encoding="utf-8") as handle:
        for index, line in enumerate(handle):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            yield StreamEvent.from_dict(json.loads(line), index=index)


def load_events(path: str | Path) -> list[StreamEvent]:
    """Load all events from a JSONL stream file."""
    return list(iter_events(Path(path)))


def cycle_events(events: Iterable[StreamEvent]) -> Iterator[StreamEvent]:
    """Repeat a finite event list forever."""
    cached = list(events)
    if not cached:
        return
    while True:
        yield from cached
