#!/usr/bin/env python3
"""Render a generic JSONL event stream as a living terminal field.

This experiment is intentionally public-safe: the bundled fixture uses
fictional sources and abstract rooms. Private adapters can produce the same
JSONL shape outside this repository, then feed only sanitized streams here.
"""

from __future__ import annotations

import argparse
import itertools
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.renderers.terminal_stage import TerminalStage
from src.streams import StreamField, load_events


DEFAULT_STREAM = ROOT / "examples" / "streams" / "demo_agents.jsonl"


def apply_cells(stage: TerminalStage, field: StreamField) -> None:
    field.resize(stage.width, stage.height)
    rows = field.render_cells()
    for y, row in enumerate(rows):
        for x, cell in enumerate(row):
            stage.set_cell(x, y, cell)


def run_text(args: argparse.Namespace) -> None:
    events = load_events(args.stream)
    field = StreamField(args.width, args.height, decay=args.decay, seed=args.seed)
    iterator = itertools.cycle(events)

    for frame in range(args.frames):
        for _ in range(args.events_per_frame):
            field.ingest(next(iterator))
        field.update()

        if frame == args.frames - 1 or args.show_all:
            if args.show_all:
                print(f"\n--- frame {frame} ---")
            print(field.render_text())


def run_live(args: argparse.Namespace) -> None:
    events = load_events(args.stream)
    field = StreamField(80, 24, decay=args.decay, seed=args.seed)
    iterator = itertools.cycle(events)

    with TerminalStage() as stage:
        frame = 0
        while args.frames <= 0 or frame < args.frames:
            for _ in range(args.events_per_frame):
                field.ingest(next(iterator))
            field.update()
            apply_cells(stage, field)
            stage.render()
            frame += 1
            time.sleep(args.delay)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stream", default=str(DEFAULT_STREAM), help="JSONL event stream")
    parser.add_argument("--frames", type=int, default=0, help="Frames to render; 0 means forever in live mode")
    parser.add_argument("--events-per-frame", type=int, default=1)
    parser.add_argument("--delay", type=float, default=0.04)
    parser.add_argument("--decay", type=float, default=0.90)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--text", action="store_true", help="Print plain text frame instead of live ANSI animation")
    parser.add_argument("--show-all", action="store_true", help="In text mode, print every frame")
    parser.add_argument("--width", type=int, default=72, help="Text mode width")
    parser.add_argument("--height", type=int, default=22, help="Text mode height")
    args = parser.parse_args()

    if args.text or not sys.stdout.isatty() or os.environ.get("CI"):
        if args.frames <= 0:
            args.frames = 24
        run_text(args)
    else:
        run_live(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
