#!/usr/bin/env python3
"""
colony_rhythm.py — which of these agents is a clock, and which is a conversation?

A colony of AI agents runs on a small cluster. Most of them wake on systemd
timers: a fixed hour, every day, whether or not anyone is there. On 2026-08-07
one of them was given a bell instead — a watcher that wakes it when a human
says its name — and for the first time an agent's activity had a *cause*
rather than a schedule.

This renders both from the same telemetry and asks whether you can tell them
apart by eye.

The answer is the piece. A timer draws vertical stripes: same column, every
day, indifferent to content. A bell draws nothing until someone rings it, and
then draws a cluster, because attention arrives in conversations rather than
in ticks. Periodicity is what a life looks like when nobody is asking for it.

Data: per-seat, per-day, per-kind event counts from the colony's own usage
plane. Only counts and coarse timestamps — no message contents, no costs, no
identifiers. A snapshot ships beside this file so the plate is reproducible
without the cluster.

    ./colony_rhythm.py --snapshot        # refresh snapshot from the live plane
    ./colony_rhythm.py                   # render from the snapshot
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
SNAPSHOT = HERE / "data" / "colony-rhythm.json"
MUSEUM = HERE.parent / "museum" / "colony-rhythm.ans"
ASSETS = HERE.parent / "docs" / "assets" / "captures" / "colony-rhythm.ans"

RESET = "\033[0m"
DIM = "\033[38;5;240m"
LABEL = "\033[38;5;250m"
WHITE = "\033[38;5;255m"

# One hue per budget pool — seats that share a pool share a colour, because
# that is the thing they actually share.
POOL_COLOR = {
    "anthropic-sub": "\033[38;5;117m",           # blue
    "anthropic-credits": "\033[38;5;111m",       # blue, dimmer
    "openai-sub": "\033[38;5;79m",               # teal
    "moonshot-sub": "\033[38;5;215m",            # amber
    "google-anthropic-bonus": "\033[38;5;180m",  # sand
    "google-sub": "\033[38;5;150m",              # green
    "nous-portal": "\033[38;5;176m",             # violet
    "xai-sub": "\033[38;5;203m",                 # red
    "local": "\033[38;5;108m",                   # moss
    "": "\033[38;5;244m",
}

# The day the colony changed how it says its own names. Production ids became
# triad keys (model-version-harness); bare aliases were refused on the write
# path. Nobody drew this line into the telemetry — it is just there.
SEAM = "2026-07-24"

DENSITY = " ▁▂▃▄▅▆▇█"
SUMMON_GLYPH = "◆"


def fetch(base: str, limit: int = 4000) -> list[dict]:
    import urllib.request

    url = f"{base}/usage/events?limit={limit}"
    with urllib.request.urlopen(url, timeout=20) as r:
        payload = json.load(r)
    return payload if isinstance(payload, list) else payload.get("events", [])


def build_snapshot(base: str) -> dict:
    """Reduce raw events to counts. Nothing identifying survives this step."""
    events = fetch(base)
    per_seat_day: dict[str, Counter] = defaultdict(Counter)
    summons: dict[str, Counter] = defaultdict(Counter)
    pools: dict[str, str] = {}

    for e in events:
        agent = (e.get("agent") or "").strip()
        ts = e.get("ts") or ""
        if not agent or len(ts) < 10:
            continue
        day = ts[:10]
        kind = e.get("kind") or ""
        per_seat_day[agent][day] += 1
        if kind == "summon":
            summons[agent][day] += 1
        meta = e.get("meta")
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
            except json.JSONDecodeError:
                meta = {}
        if isinstance(meta, dict) and meta.get("pool"):
            pools.setdefault(agent, meta["pool"])

    return {
        "generated_from": "colony usage plane (counts only)",
        "seats": {
            seat: {
                "pool": pools.get(seat, ""),
                "days": dict(days),
                "summons": dict(summons.get(seat, {})),
            }
            for seat, days in per_seat_day.items()
        },
    }


def day_range(snapshot: dict) -> list[str]:
    all_days = sorted({d for s in snapshot["seats"].values() for d in s["days"]})
    if not all_days:
        return []
    start = date.fromisoformat(all_days[0])
    end = date.fromisoformat(all_days[-1])
    span = (end - start).days
    return [(start + timedelta(days=i)).isoformat() for i in range(span + 1)]


def render(snapshot: dict, *, min_events: int = 1) -> str:
    days = day_range(snapshot)
    if not days:
        return "no data"

    seats = {
        name: row
        for name, row in snapshot["seats"].items()
        if sum(row["days"].values()) >= min_events
    }
    # Sort by the day each seat FIRST appears, then by volume. Sorting by
    # activity would have buried the actual subject: ordered by birth, the
    # renaming shows up as a staircase, because eleven rows start on one day.
    def first_day(name: str) -> str:
        return min(seats[name]["days"]) if seats[name]["days"] else "9999"

    order = sorted(seats, key=lambda n: (first_day(n), -sum(seats[n]["days"].values())))
    peak = max(
        (c for row in seats.values() for c in row["days"].values()), default=1
    )
    width = len(days)
    name_w = max(len(n) for n in order) + 1

    seam_col = days.index(SEAM) if SEAM in days else -1

    out = []
    add = out.append
    add("")
    add(f"{WHITE}  THE UNDERSTORY · {width} DAYS · ORDERED BY BIRTH{RESET}")
    add(f"{DIM}  one row per seat · one column per day · height = events that day{RESET}")
    add(f"{DIM}  colour = shared budget pool · {SUMMON_GLYPH} = woken by a human saying its name{RESET}")
    add("")

    prev_first = None
    for name in order:
        row = seats[name]
        colour = POOL_COLOR.get(row["pool"], POOL_COLOR[""])
        this_first = first_day(name)

        # A rule where the naming changed. Eleven rows begin on the far side.
        if seam_col >= 0 and prev_first is not None \
                and prev_first < SEAM <= this_first:
            add(f"  {' ' * name_w}{DIM}{'╌' * seam_col}┤{'╌' * (width - seam_col - 1)}{RESET}"
                f"  {LABEL}← {SEAM}: triad ids{RESET}")
        prev_first = this_first

        cells = []
        for i, d in enumerate(days):
            n = row["days"].get(d, 0)
            if row["summons"].get(d):
                cells.append(f"{WHITE}{SUMMON_GLYPH}{RESET}{colour}")
            elif n == 0:
                cells.append(f"{DIM}{'┊' if i == seam_col else '·'}{RESET}{colour}")
            else:
                idx = min(len(DENSITY) - 1, 1 + int((n / peak) * (len(DENSITY) - 2)))
                cells.append(DENSITY[idx])
        total = sum(row["days"].values())
        add(f"  {LABEL}{name:<{name_w}}{RESET}{colour}{''.join(cells)}{RESET}"
            f"  {DIM}{total:>4}{RESET}")

    add(f"  {' ' * name_w}{DIM}└{'─' * (width - 2)}┘{RESET}")
    add(f"  {' ' * name_w}{DIM}{days[0]}{' ' * max(1, width - 21)}{days[-1]}{RESET}")
    add("")

    pools_seen = sorted({r["pool"] for r in seats.values() if r["pool"]})
    legend = "  ".join(
        f"{POOL_COLOR.get(p, POOL_COLOR[''])}██{RESET}{DIM} {p}{RESET}" for p in pools_seen
    )
    add(f"  {legend}")
    add("")
    return "\n".join(out)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--snapshot", action="store_true",
                   help="refresh the snapshot from the live usage plane")
    p.add_argument("--base", default=os.environ.get("GARDEN_COMMS_URL", ""),
                   help="usage-plane base URL (env GARDEN_COMMS_URL)")
    p.add_argument("--min-events", type=int, default=1,
                   help="hide seats with fewer events than this")
    args = p.parse_args()

    if args.snapshot:
        if not args.base:
            print("need --base or GARDEN_COMMS_URL to refresh the snapshot",
                  file=sys.stderr)
            return 1
        snap = build_snapshot(args.base)
        SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
        SNAPSHOT.write_text(json.dumps(snap, indent=2, sort_keys=True) + "\n",
                            encoding="utf-8")
        print(f"wrote {SNAPSHOT.relative_to(HERE.parent)} "
              f"({len(snap['seats'])} seats)")

    if not SNAPSHOT.is_file():
        print("no snapshot — run with --snapshot first", file=sys.stderr)
        return 1

    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    plate = render(snapshot, min_events=args.min_events)
    print(plate)

    for target in (MUSEUM, ASSETS):
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(plate + "\n", encoding="utf-8")
    print(f"{DIM}wrote museum/ and docs/assets/captures/colony-rhythm.ans{RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
