#!/usr/bin/env python3
"""Decaying event field for stream-based visualizations."""

from __future__ import annotations

import colorsys
import hashlib
import math
import random
from dataclasses import dataclass
from typing import Dict, Iterable, Tuple

from src.renderers.terminal_stage import CellState

from .events import StreamEvent


RGB = Tuple[int, int, int]


@dataclass
class Pulse:
    """A visible particle emitted by a stream event."""

    x: float
    y: float
    vx: float
    vy: float
    energy: float
    hue: float
    source: str
    kind: str
    age: int = 0


class StreamField:
    """Turns abstract events into fading terminal particles."""

    def __init__(
        self,
        width: int,
        height: int,
        *,
        decay: float = 0.88,
        drift: float = 0.12,
        seed: int | None = None,
    ):
        self.width = width
        self.height = height
        self.decay = decay
        self.drift = drift
        self.rng = random.Random(seed)
        self.pulses: list[Pulse] = []
        self.source_hues: Dict[str, float] = {}
        self.room_centers: Dict[str, tuple[float, float]] = {}

    def resize(self, width: int, height: int) -> None:
        self.width = width
        self.height = height

    def ingest(self, event: StreamEvent) -> None:
        """Emit one or more particles for an event."""
        x, y = self._event_position(event)
        hue = self.source_hue(event.source)
        count = max(1, min(5, int(math.ceil(event.intensity * 2))))
        for _ in range(count):
            angle = self.rng.random() * math.tau
            speed = self.drift * (0.5 + self.rng.random())
            self.pulses.append(
                Pulse(
                    x=x + self.rng.uniform(-1.0, 1.0),
                    y=y + self.rng.uniform(-0.5, 0.5),
                    vx=math.cos(angle) * speed,
                    vy=math.sin(angle) * speed * 0.45,
                    energy=max(0.2, event.intensity),
                    hue=(hue + self._kind_shift(event.kind)) % 1.0,
                    source=event.source,
                    kind=event.kind,
                )
            )

    def update(self) -> None:
        """Advance particles and fade old energy."""
        kept: list[Pulse] = []
        for pulse in self.pulses:
            pulse.age += 1
            pulse.x = (pulse.x + pulse.vx) % max(1, self.width)
            pulse.y = (pulse.y + pulse.vy) % max(1, self.height)
            pulse.vx += self.rng.uniform(-0.02, 0.02)
            pulse.vy += self.rng.uniform(-0.01, 0.01)
            pulse.energy *= self.decay
            if pulse.energy > 0.035:
                kept.append(pulse)
        self.pulses = kept

    def render_cells(self) -> list[list[CellState]]:
        """Render current field state as a grid of CellState objects."""
        accum: list[list[dict[str, float]]] = [
            [self._empty_accum() for _ in range(self.width)]
            for _ in range(self.height)
        ]

        for pulse in self.pulses:
            x = int(round(pulse.x)) % max(1, self.width)
            y = int(round(pulse.y)) % max(1, self.height)
            cell = accum[y][x]
            energy = min(3.0, pulse.energy)
            cell["energy"] += energy
            cell["r"] += energy * math.cos(pulse.hue * math.tau)
            cell["i"] += energy * math.sin(pulse.hue * math.tau)

        rows: list[list[CellState]] = []
        for y in range(self.height):
            row: list[CellState] = []
            for x in range(self.width):
                row.append(self._cell_from_accum(accum[y][x]))
            rows.append(row)
        return rows

    def render_text(self) -> str:
        """Render a dependency-free text preview without ANSI color."""
        rows = self.render_cells()
        return "\n".join("".join(cell.char for cell in row) for row in rows)

    def source_hue(self, source: str) -> float:
        if source not in self.source_hues:
            self.source_hues[source] = _hash01(source)
        return self.source_hues[source]

    def _event_position(self, event: StreamEvent) -> tuple[float, float]:
        if event.x is not None and event.y is not None:
            return event.x * (self.width - 1), event.y * (self.height - 1)
        if event.room not in self.room_centers:
            self.room_centers[event.room] = (
                2 + _hash01(event.room + ":x") * max(1, self.width - 4),
                1 + _hash01(event.room + ":y") * max(1, self.height - 2),
            )
        cx, cy = self.room_centers[event.room]
        source_angle = _hash01(event.source + event.room) * math.tau
        radius = 2.0 + _hash01(event.source) * min(self.width, self.height) * 0.12
        return (
            (cx + math.cos(source_angle) * radius) % max(1, self.width),
            (cy + math.sin(source_angle) * radius * 0.5) % max(1, self.height),
        )

    def _kind_shift(self, kind: str) -> float:
        shifts = {
            "message": 0.00,
            "status": 0.06,
            "question": 0.13,
            "artifact": 0.22,
            "heartbeat": 0.33,
            "latency": 0.41,
            "temperature": 0.52,
            "wireless": 0.61,
            "weather": 0.72,
            "wind": 0.77,
            "precipitation": 0.80,
            "alert": 0.84,
        }
        return shifts.get(kind, _hash01(kind) * 0.18)

    def _empty_accum(self) -> dict[str, float]:
        return {"energy": 0.0, "r": 0.0, "i": 0.0}

    def _cell_from_accum(self, cell: dict[str, float]) -> CellState:
        energy = cell["energy"]
        if energy <= 0.02:
            return CellState(char=" ", fg_color=(30, 30, 36), bg_color=(0, 0, 0))

        hue = math.atan2(cell["i"], cell["r"]) / math.tau
        intensity = max(0.0, min(1.0, energy / 2.5))
        char = glyph_for_intensity(intensity)
        fg = hsv_to_rgb(hue % 1.0, 0.70 + intensity * 0.30, 0.35 + intensity * 0.65)
        bg = hsv_to_rgb((hue + 0.5) % 1.0, 0.55, intensity * 0.16)
        return CellState(char=char, fg_color=fg, bg_color=bg)


def glyph_for_intensity(intensity: float) -> str:
    if intensity <= 0:
        return " "
    glyphs = ".·:;*oO0@"
    idx = min(len(glyphs) - 1, int(intensity * (len(glyphs) - 1)))
    return glyphs[idx]


def hsv_to_rgb(h: float, s: float, v: float) -> RGB:
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (int(r * 255), int(g * 255), int(b * 255))


def _hash01(value: str) -> float:
    digest = hashlib.sha256(value.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") / float(2**64 - 1)


def run_events(field: StreamField, events: Iterable[StreamEvent], frames: int) -> None:
    """Advance a field through a fixed number of events/frames."""
    iterator = iter(events)
    for _ in range(frames):
        try:
            field.ingest(next(iterator))
        except StopIteration:
            pass
        field.update()
