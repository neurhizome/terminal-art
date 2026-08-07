#!/usr/bin/env python3
"""Render The Cascade's two findings as one ANSI plate.

Top: shared pool over time, one band per regime, single seed, perfect roster.
Bottom: survival against roster leakage — the band where the redundant guard
stops being redundant.
"""

import importlib.util
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))

_spec = importlib.util.spec_from_file_location("casc", os.path.join(HERE, "cascade.py"))
casc = importlib.util.module_from_spec(_spec)
sys.modules["casc"] = casc
_spec.loader.exec_module(casc)

RESET = "\033[0m"
DIM = "\033[38;5;240m"
LABEL = "\033[38;5;250m"
COLOR = {
    "none": "\033[38;5;203m",     # red
    "depth": "\033[38;5;215m",    # amber
    "defang": "\033[38;5;79m",    # teal
    "both": "\033[38;5;117m",     # blue
}
BLOCKS = " ▁▂▃▄▅▆▇█"
WIDTH, TICKS, POOL = 78, 4000, 240.0


def trace(regime, seed):
    colony = casc.Colony(regime, width=120, height=32, pool=POOL, rate_cap=0,
                         human_rate=0.02, regen=0.25, defang_miss=0.0,
                         rng=__import__("random").Random(seed))
    out = []
    step = max(1, TICKS // WIDTH)
    for t in range(TICKS):
        colony.tick(t)
        if t % step == 0:
            out.append(max(0.0, colony.pool))
    return out[:WIDTH]


def band(values):
    return "".join(
        BLOCKS[min(len(BLOCKS) - 1, int((v / POOL) * (len(BLOCKS) - 1) + 0.5))]
        for v in values
    )


lines = []
add = lines.append
add("")
add(f"{LABEL}  THE CASCADE — one relay, one shared budget, eight seats{RESET}")
add(f"{DIM}  shared pool over 4000 ticks · seed 3 · roster complete{RESET}")
add("")
for regime in casc.REGIMES:
    values = trace(regime, 3)
    dead = "" if values[-1] > 0 else f"  {DIM}← spent{RESET}"
    add(f"  {COLOR[regime]}{regime:<7}{RESET} {COLOR[regime]}{band(values)}{RESET}{dead}")
add(f"{DIM}         └{'─' * (WIDTH - 2)}┘{RESET}")
add(f"{DIM}          t=0{' ' * (WIDTH - 14)}t=4000{RESET}")
add("")
add(f"{LABEL}  the redundant guard, and where it stops being redundant{RESET}")
add(f"{DIM}  colonies surviving 4000 ticks, 24 seeds, by roster leak rate{RESET}")
add("")
add(f"{DIM}  leak    defang only            defang + depth{RESET}")
for miss in (0.00, 0.02, 0.05, 0.08, 0.10):
    cells = []
    for regime in ("defang", "both"):
        runs = [
            casc.run_headless(regime, TICKS, s, pool=POOL, rate_cap=0,
                              human_rate=0.02, regen=0.25, defang_miss=miss)
            for s in range(24)
        ]
        alive = sum(1 for c in runs if c.stats.extinct_at is None)
        bar = "█" * alive + f"{DIM}·{RESET}" * (24 - alive)
        cells.append((alive, bar))
    mark = f"  {LABEL}← the band{RESET}" if miss == 0.05 else ""
    add(f"  {miss:>4.0%}   {COLOR['defang']}{cells[0][1]}{RESET} {cells[0][0]:>2}/24   "
        f"{COLOR['both']}{cells[1][1]}{RESET} {cells[1][0]:>2}/24{mark}")
add("")

plate = "\n".join(lines)
print(plate)
out = os.path.join(HERE, "..", "museum", "cascade-the-band.ans")
with open(out, "w", encoding="utf-8") as fh:
    fh.write(plate + "\n")
print(f"{DIM}wrote {os.path.normpath(out)}{RESET}")
