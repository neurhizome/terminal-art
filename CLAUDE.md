# CLAUDE.md — terminal-art (asciicology)

This file documents the codebase structure, development conventions, and workflows for AI assistants working in this repository.

## Project Overview

**terminal-art** (also called *asciicology*) is a composable Python toolkit for creating animated terminal graphics, memetic cellular automata, and emergent pattern experiments. The core design philosophy is **modular composition**: independent components snap together to build complex visualizations from simple rules.

- **License**: MIT © 2025 neurhizome
- **Runtime**: Python 3.7+, near-zero dependencies (only `wcwidth` optional)
- **Targets**: Any POSIX terminal with UTF-8 and truecolor support (Linux, macOS, iSH/iOS)

---

## Repository Structure

```
terminal-art/
├── src/                          # Core modular toolkit (~3,073 LOC)
│   ├── automata/                 # Walker entities and population management
│   │   ├── walker.py             # Base Walker class (position + genome + age)
│   │   ├── spawner.py            # Population manager (add/remove/breed walkers)
│   │   └── behaviors.py         # Pluggable movement strategies
│   ├── genetics/                 # Memetic trait system
│   │   ├── genome.py             # HSV color genome with inheritance
│   │   ├── inheritance.py        # Parent→child trait flow
│   │   └── speciation.py         # Reproductive barriers (hue distance)
│   ├── fields/                   # 2D grid-based spatial systems
│   │   ├── base.py               # Abstract Field interface
│   │   ├── diffusion.py          # Scent trails / chemical diffusion
│   │   ├── territory.py          # Chunked ownership tracking
│   │   └── energy.py             # Excitable medium with cascade dynamics
│   ├── events/                   # Temporal perturbation system
│   │   ├── event.py              # Base Event class
│   │   ├── catalog.py            # Pre-built event library (AESTHETIC_POOL, CHAOS_POOL)
│   │   └── scheduler.py          # Event timing and triggering
│   ├── glyphs/                   # Probabilistic Unicode character selection
│   │   ├── picker.py             # GlyphPicker (load DB, query by direction/style)
│   │   └── direction.py          # Direction enum (N, NE, E, SE, S, SW, W, NW, NONE)
│   ├── renderers/                # Terminal display layer
│   │   └── terminal_stage.py     # TerminalStage: double-buffered full-screen canvas
│   └── utils/
│       └── colors.py             # HSV/RGB conversion, circular hue mean
├── experiments/                  # Composable experiment scripts (reference implementations)
│   ├── simple_walkers.py         # Minimal example: walkers + colors (~30 lines)
│   ├── memetic_territories.py    # Full-featured: genetics + fields + events
│   ├── color_speciation.py       # Reproductive barriers creating color species
│   ├── gradient_flow.py          # Aesthetic mode: flowing color gradients
│   ├── predator_prey.py          # Lotka-Volterra dynamics (green prey vs red predators)
│   └── README.md                 # Experiment composition guide
├── demos/                        # Standalone pre-modular demonstration scripts (20+)
│   ├── ascii_waves.py            # Cellular automata waves (most feature-rich demo)
│   ├── braille_galaxies.py       # Braille pattern animations
│   ├── walker_connect.py         # Animated connector walkers
│   ├── morphing_connectors_demo.py
│   └── ...                       # Other standalone visualizations
├── tools/                        # Glyph database builders and Unicode scanners
│   ├── build_comprehensive_db.py # Generates 1,742-glyph full database
│   ├── build_optimized_db.py     # Mobile-optimized 720-glyph subset
│   └── unicode_scanner.py        # Scans Unicode ranges for character properties
├── docs/                         # Documentation, blog posts, concept articles
│   ├── concepts/                 # stigmergy.md, diffusion-memory.md, index.md
│   └── _posts/                   # Session exploration blog posts (001–004+)
├── sketches/                     # Quick experiment templates
├── gallery/                      # Screenshot collection
├── museum/                       # Captured ANSI animation outputs
├── scripts/
│   └── speciation_capture.py     # Records animations to ANSI format
├── glyph_database.json           # Essential glyph set (~9.6 KB)
├── glyph_database_optimized.json # Mobile-optimized (~136 KB, 720 glyphs)
├── glyph_database_full.json      # Full database (~194 KB, 1,742 glyphs)
├── requirements.txt              # Runtime deps (wcwidth only)
├── requirements-min.txt          # Bare minimum
├── requirements-full.txt         # Future dev (blessed, rich, typer)
├── README.md                     # Main project overview and API examples
├── ARCHITECTURE.md               # Detailed modular design patterns
├── OPTIMIZATION.md               # Performance tuning guidelines
├── PLAYGROUND.md                 # Creative exploration guide
└── BLOG_GUIDE.md                 # Blog post generation documentation
```

---

## Core Abstractions

The toolkit is built on five composable abstractions. Understanding these is essential before making any changes.

### 1. Walker (`src/automata/walker.py`)

An entity with **position + genetic traits**. Behavior is injected, not hardcoded.

```python
class Walker:
    x, y        # Terminal position
    genome      # Genetic traits (color_h, vigor, etc.)
    age         # Tick counter
    vigor       # Fitness weight (affects inheritance)

    def move(self, dx, dy, width, height, wrap=True)
    def deposit(self, field)           # Leave scent/energy in a field
    def sense(self, field)             # Read field values
    def reproduce_with(self, other)    # Returns child Walker
    def can_breed_with(self, other)    # Checks reproductive barrier
```

### 2. Field (`src/fields/base.py`)

An **abstract 2D grid** that stores and evolves values. All field types implement this interface.

```python
class Field(ABC):
    def get(self, x, y) -> value
    def set(self, x, y, value)
    def update()           # Apply dynamics (diffusion, decay, cascade)
    def render()           # Returns grid of (char, fg_color, bg_color)
```

**Concrete implementations:**
- `DiffusionField` — values spread to neighbors and decay each tick
- `TerritoryField` — chunked ownership tracking (vigor-weighted)
- `EnergyField` — excitable medium with cascade dynamics
- `ConnectionField` — NESW bitmasks for connector-walker rendering

### 3. Genome (`src/genetics/genome.py`)

A **memetic trait container** where color is the primary (visible) genetic marker.

```python
class Genome:
    color_h    # Hue [0, 1) — the visible phenotype
    vigor      # Fitness weight — affects inheritance dominance
    traits     # Extensible dict for custom properties

    def reproduce_with(self, other, mutation_rate=0.03) -> Genome
    def distance_to(self, other) -> float   # Circular hue distance [0, 0.5]
```

Reproduction uses **vigor-weighted circular mean** of hue + Gaussian drift. The `distance_to` method enables speciation (reproductive barriers).

### 4. Event (`src/events/event.py`)

**Perturbative dynamics** that temporarily modify system parameters.

```python
class Event:
    duration, strength, target_param
    elapsed

    def apply(self, system)      # Modifies system dict in-place
    def is_finished() -> bool
```

Pre-built events in `catalog.py`: `SpawnRateBurst`, `GlobalColorShift`, `VigorWave`, `Extinction`, and more. Use `AESTHETIC_POOL` for calm events, `CHAOS_POOL` for dramatic ones.

### 5. TerminalStage (`src/renderers/terminal_stage.py`)

A **double-buffered full-screen canvas** for flicker-free rendering.

```python
stage = TerminalStage()
stage.width, stage.height    # Terminal dimensions
stage.set_cell(x, y, char, fg_color, bg_color)
stage.render_field(field)    # Composites a Field onto the canvas
stage.render_walkers(walkers)
stage.flush()                # Writes only changed cells to terminal
```

Uses 24-bit truecolor ANSI escape codes and handles terminal resize.

---

## Composition Patterns

New experiments are built by composing the five abstractions. Reference `experiments/` for working examples.

### Minimal (walkers only)
```python
from src.automata import Spawner
from src.genetics import Genome

spawner = Spawner(max_walkers=500, width=80, height=24)
spawner.spawn_random(genome=Genome(color_h=0.5))

for walker in spawner.walkers:
    dx, dy = behavior.get_move(walker.x, walker.y)
    walker.move(dx, dy, 80, 24, wrap=True)
```

### Field-driven dynamics
```python
from src.fields import DiffusionField

scent = DiffusionField(width, height, diffusion_rate=0.2, decay_rate=0.95)
for walker in spawner.walkers:
    scent.deposit(walker.x, walker.y, walker.vigor * 0.5)
scent.update()
```

### Full composition (events + genetics + fields)
```python
from src.automata import Spawner
from src.genetics import Genome
from src.fields import DiffusionField, TerritoryField
from src.events import EventScheduler, AESTHETIC_POOL
from src.renderers import TerminalStage

stage = TerminalStage()
spawner = Spawner(max_walkers=300, width=stage.width, height=stage.height)
scent = DiffusionField(stage.width, stage.height)
territory = TerritoryField(stage.width, stage.height, chunk_size=8)
events = EventScheduler()

while True:
    events.update({'spawner': spawner, 'field': scent})
    for walker in spawner.walkers:
        scent.deposit(walker.x, walker.y, walker.vigor)
        territory.claim(walker)
        walker.move(dx, dy, stage.width, stage.height, wrap=True)
    scent.update()
    territory.update()
    stage.render_field(territory)
    stage.render_walkers(spawner.walkers)
    stage.flush()
```

**Data flow:**
```
Walkers → deposit() → Fields → update() → render() → Stage → Display
   ↑                                         ↓
   └──────────── sense() ←──────────────────┘
```

---

## Code Conventions

### Language & Style
- **Python 3.7+** with type hints throughout
- **Snake_case** for functions, variables, module names
- **PascalCase** for classes
- **Dataclasses** for immutable state containers (`WalkerState`, `GlyphInfo`)
- **ABC** (Abstract Base Classes) for extensible interfaces
- Comprehensive docstrings at module, class, and method level

### Module Exports
Each subpackage uses explicit `__init__.py` exports via `__all__`:
```python
# src/automata/__init__.py
from .walker import Walker, WalkerState
from .spawner import Spawner
from .behaviors import RandomWalk, LevyFlight, GradientFollow
__all__ = ['Walker', 'WalkerState', 'Spawner', 'RandomWalk', ...]
```

Always import from the package, not sub-modules directly:
```python
from src.automata import Walker, Spawner          # correct
from src.automata.walker import Walker            # avoid in experiments
```

### Behavior Injection (not inheritance)
Behaviors are **always passed in** — never subclass Walker to add movement:
```python
# Correct: inject behavior
behavior = GradientFollow('scent', attraction=True)
dx, dy = behavior.get_move(walker.x, walker.y, field=scent_field)

# Wrong: subclass for behavior
class ChemotaxisWalker(Walker): ...
```

### Graceful Degradation
Components fall back gracefully when optional deps are absent (e.g., missing glyphs fall back to space character). Do not add hard runtime requirements.

### Colors
Colors are represented as **HSV tuples `(h, s, v)`** internally, converted to RGB for ANSI output via `src/utils/colors.py`. Hue `color_h` is a float in `[0, 1)` using circular arithmetic.

---

## Development Workflow

### Environment Setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt   # just wcwidth
```

### Running Experiments
```bash
# Minimal — walkers + colors
python3 experiments/simple_walkers.py --walkers 100

# Full-featured with events
python3 experiments/memetic_territories.py --initial-walkers 20 --max-walkers 300 --events

# Color speciation
python3 experiments/color_speciation.py

# Predator-prey dynamics
python3 experiments/predator_prey.py

# Standalone demo
python3 demos/ascii_waves.py --rows 200 --delay 0.01 --style heavy
```

### Building Glyph Databases
```bash
# Full 1,742-glyph database
python3 tools/build_comprehensive_db.py --all-ranges -o glyph_database_full.json

# Mobile-optimized 720-glyph subset
python3 tools/build_optimized_db.py -o glyph_database_optimized.json

# Scan a specific Unicode range
python3 tools/unicode_scanner.py --start 0x2500 --end 0x259F --outfile box_drawing.json
```

### Capturing Animations
```bash
python3 scripts/speciation_capture.py   # Saves ANSI files to museum/
```

### No Formal Test Suite
There is no automated test runner. Validation is done by:
1. Running the experiments directly and observing output
2. Checking `experiments/README.md` for expected behaviors
3. Using `PLAYGROUND.md` for guided exploration

When adding new modules, write a minimal experiment in `experiments/` or `sketches/` to demonstrate correct behavior.

---

## Performance Guidelines

From `OPTIMIZATION.md` and measured benchmarks:

| Scale | Walkers | Fields | Target FPS |
|-------|---------|--------|-----------|
| Small | < 100 | none | 60+ FPS |
| Medium | 100–500 | 1–2 | 20–30 FPS |
| Large | 500+ | multiple | 10–20 FPS |

Key rules:
- `TerminalStage.flush()` only writes **changed cells** — avoid forcing full redraws
- `TerritoryField` uses **chunked** ownership (8×8 default) to avoid per-cell tracking
- `DiffusionField.update()` uses NumPy-style array ops when available, pure Python fallback otherwise
- Use `glyph_database_optimized.json` (720 glyphs) on mobile/low-power terminals
- Prefer `wrap=True` over edge-bounce for lower branch cost in the walker loop

---

## Glyph System

The glyph system (`src/glyphs/`) provides probabilistic Unicode character selection with 1,742 glyphs across 11 Unicode ranges.

```python
from src.glyphs import GlyphPicker, Direction

picker = GlyphPicker.from_json("glyph_database_full.json")

# Probabilistic — same query returns varied characters
char = picker.get(direction=Direction.E, intensity=0.7)

# Filtered by style
arrow  = picker.get(direction=Direction.NE, style="arrow")
clock  = picker.get(direction=Direction.SE, style="clock")
braille = picker.get(direction=Direction.S,  style="braille", intensity=0.3)
```

**Database files** (choose based on environment):
- `glyph_database.json` — essential set, smallest
- `glyph_database_optimized.json` — 720 glyphs, mobile-friendly
- `glyph_database_full.json` — 1,742 glyphs, all ranges

**Direction enum values**: `N, NE, E, SE, S, SW, W, NW, NONE`

---

## iSH (iOS Alpine Linux) Setup

```bash
apk update && apk add python3 py3-pip ncurses git
python3 -m venv venv && source venv/bin/activate
export TERM=xterm-256color
export COLORTERM=truecolor
export PYTHONIOENCODING=utf-8
pip install wcwidth
python3 demos/ascii_waves.py --rows 300 --delay 0.015 --style light --bg-set dots
```

Use `glyph_database_optimized.json` on iOS for best performance.

---

## Key Files for AI Assistants

When investigating or modifying the codebase, these are the most important files:

| File | Purpose |
|------|---------|
| `src/automata/walker.py` | Walker entity — start here for movement/genetics questions |
| `src/automata/spawner.py` | Population management — add/remove/breed walkers |
| `src/automata/behaviors.py` | All movement strategies (RandomWalk, LevyFlight, GradientFollow, etc.) |
| `src/genetics/genome.py` | Color genome and reproduction logic |
| `src/fields/base.py` | Abstract Field interface — all field types extend this |
| `src/fields/diffusion.py` | Most-used field: scent/chemical diffusion |
| `src/events/catalog.py` | Pre-built events and event pools |
| `src/renderers/terminal_stage.py` | Rendering pipeline and display layer |
| `src/glyphs/picker.py` | Glyph selection API |
| `src/utils/colors.py` | Color math (HSV↔RGB, circular hue mean) |
| `experiments/memetic_territories.py` | Best reference for full-stack composition |
| `experiments/simple_walkers.py` | Best reference for minimal composition |
| `ARCHITECTURE.md` | Design patterns and module contracts |

---

## Common Tasks

### Add a new movement behavior
1. Open `src/automata/behaviors.py`
2. Subclass the behavior base class and implement `get_move(x, y, **kwargs) -> (dx, dy)`
3. Export from `src/automata/__init__.py`
4. Demonstrate in a sketch or experiment

### Add a new field type
1. Subclass `Field` from `src/fields/base.py`
2. Implement `get`, `set`, `update`, and optionally `render`
3. Export from `src/fields/__init__.py`

### Add a new event
1. Subclass `Event` from `src/events/event.py`
2. Implement `apply(self, system)` — `system` is a dict with keys like `'spawner'`, `'field'`, `'config'`
3. Add to `catalog.py` and optionally to `AESTHETIC_POOL` or `CHAOS_POOL`

### Create a new experiment
1. Copy `experiments/simple_walkers.py` as a starting point
2. Import only the modules you need
3. Keep total experiment length under 100 lines by relying on the modular API
4. Add CLI args with `argparse` following the pattern in existing experiments

---

## Documentation Files

| File | Contents |
|------|---------|
| `README.md` | Quick start, full API reference, CLI options |
| `ARCHITECTURE.md` | Design patterns, module contracts, composition examples |
| `OPTIMIZATION.md` | Performance tuning and benchmarks |
| `PLAYGROUND.md` | Creative exploration guide, parameter tuning suggestions |
| `BLOG_GUIDE.md` | How to write session blog posts in `docs/_posts/` |
| `docs/concepts/` | Conceptual articles (stigmergy, diffusion-memory) |
| `experiments/README.md` | Experiment composition patterns and performance table |
