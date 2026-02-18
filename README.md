# terminal-art (asciicology) — Modular Terminal Automata Toolkit

A **composable toolkit** for creating animated terminal graphics, memetic automata, and emergent pattern experiments. Built from **modular building blocks** that snap together like LEGO.

Most components are **dependency-free** and run on any POSIX terminal, including **iSH on iOS**.

## Features

### Core Modules (NEW!)

- **🧬 Genetics** (`src.genetics`) - Memetic color genomes with inheritance and drift
- **🚶 Automata** (`src.automata`) - Walker entities with pluggable behaviors
- **🌊 Fields** (`src.fields`) - Diffusion, territory tracking, energy grids
- **⚡ Events** (`src.events`) - Perturbative dynamics for temporal variation
- **🎨 Renderers** (`src.renderers`) - Terminal Stage with double-buffering
- **✨ Glyphs** (`src.glyphs`) - Probabilistic character selection (1,742 glyphs)

### Philosophy

- **Modular composition** - Mix and match components to build experiments
- **Dependency injection** - Behaviors are injected, not inherited
- **Colors as memes** - RGB traits flow through populations via reproduction
- **Emergence over programming** - Simple rules create complex patterns

## Project Structure

```
terminal-art/
├── src/                # Modular toolkit components
│   ├── genetics/       # Memetic color genomes (NEW!)
│   ├── automata/       # Walkers + behaviors + spawner (NEW!)
│   ├── fields/         # Diffusion, territory, energy (NEW!)
│   ├── events/         # Event system + catalog (NEW!)
│   ├── glyphs/         # Probabilistic glyph selection
│   ├── renderers/      # Terminal rendering (TerminalStage)
│   └── utils/          # Shared utilities
├── experiments/        # Composable experiments (NEW!)
│   ├── simple_walkers.py          # Minimal (30 lines)
│   ├── memetic_territories.py     # Full-featured (100 lines)
│   └── README.md                  # Experiment guide
├── demos/              # Standalone demos (pre-modular)
│   ├── walker_*.py     # Walker animations
│   ├── braille_*.py    # Braille patterns
│   └── ascii_*.py      # ASCII/box-drawing
├── tools/              # Database builders + scanners
│   ├── build_comprehensive_db.py  # 1,742 glyph database
│   ├── build_optimized_db.py      # Mobile-optimized (720 glyphs)
│   └── unicode_scanner.py         # Scan Unicode ranges
└── ARCHITECTURE.md     # Modular design doc (NEW!)
```

## Quick Start

### 1. Set up virtual environment (recommended)

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Try modular experiments (NEW!)

**Simple walkers (30 lines, just movement + colors):**
```bash
python3 experiments/simple_walkers.py --walkers 100
```

**Memetic territories (full-featured: genetics + fields + events):**
```bash
# With perturbative events
python3 experiments/memetic_territories.py --initial-walkers 20 --max-walkers 300 --events

# Stable (no events)
python3 experiments/memetic_territories.py --initial-walkers 30 --max-walkers 500

# High chaos (fast spawning + events)
python3 experiments/memetic_territories.py --spawn-rate 0.15 --events
```

See `experiments/README.md` for more examples and patterns.

### 3. Try standalone demos

**Animated connector walker:**
```bash
python3 demos/walker_connect_color16.py --style heavy --wrap
```

**Cellular automata waves:**
```bash
python3 demos/ascii_waves.py --rows 200 --delay 0.01 --style heavy --bg-glyph "·"
```

**Morphing connectors:**
```bash
python3 demos/morphing_connectors_demo.py
```

**Braille galaxies:**
```bash
python3 demos/braille_galaxies.py
```

### 3. Scan Unicode for glyphs

```bash
# Scan box-drawing characters
python3 tools/unicode_scanner.py --start 0x2500 --end 0x259F --outfile box_drawing.json

# View results
python3 tools/glyph_viewer.py box_drawing.json
```

## iSH Setup (Alpine iOS) — Truecolor & UTF‑8

In iSH (iOS):
```bash
apk update
apk add python3 py3-pip ncurses git
python3 -m venv venv
source venv/bin/activate
export TERM=xterm-256color
export COLORTERM=truecolor
export PYTHONIOENCODING=utf-8
```

Run a demo:
```bash
python3 demos/ascii_waves.py --rows 300 --delay 0.015 --style light --bg-set dots
```

> **Tip:** iSH inherits iOS font rendering. For best alignment, use monospaced fonts that include box-drawing & braille characters. If glyphs look misaligned, try different styles or scan your font with `tools/unicode_scanner.py`.

## Concepts
- **Connector style**: maps N/E/S/W bitmasks → box‑drawing (or ASCII) characters.
- **Glyph sets**: named bags you can sprinkle as extras or use for background.
- **Foreground/Background glyphs**: override defaults for “on”/“off” cells.
- **Cell width auto‑sizing**: expands to fit the longest chosen glyph (multi‑char OK).

## CLI
Run `python3 ascii_waves.py -h` for all options. Highlights:
- `--style`: light | heavy | double | rounded | ascii
- `--bg-glyph` or `--bg-set`: choose the background glyph(s) when the CA bit is 0
- `--fg-glyph`: force a single glyph for CA bit 1 (otherwise connectors are used)
- `--extras` + `--extra-prob`: sprinkle from a glyph set (e.g., `dots,angles,blocks,braille-lite`)
- `--rule`, `--burst`, `--jitter`, `--rows`, `--delay`, `--seed`
- `--no-color`: disable ANSI colors entirely

## Modular Toolkit API

### Building Experiments from Components

Create custom automata experiments by composing modular building blocks:

#### 1. **Walkers with Genetic Traits**

```python
from src.automata import Walker, Spawner
from src.genetics import Genome

# Create spawner
spawner = Spawner(max_walkers=500, width=80, height=24)

# Spawn walker with genetic color
genome = Genome(color_h=0.5, vigor=1.2)  # Hue=cyan, high fitness
walker = Walker(x=40, y=12, genome=genome)
spawner.add(walker)

# Reproduce with another walker
partner = spawner.walkers[0]
if walker.can_breed_with(partner):  # Check genetic compatibility
    child = spawner.spawn_from_parents(walker, partner, mutation_rate=0.03)
```

#### 2. **Pluggable Movement Behaviors**

```python
from src.automata.behaviors import RandomWalk, GradientFollow, LevyFlight

# Inject behavior (not inherited!)
behavior = RandomWalk(eight_way=True)
dx, dy = behavior.get_move(walker.x, walker.y)
walker.move(dx, dy, width, height, wrap=True)

# Hot-swap: Change to gradient following
behavior = GradientFollow('scent', attraction=True)
dx, dy = behavior.get_move(walker.x, walker.y, field=scent_field)
```

#### 3. **Fields: Diffusion, Territory, Energy**

```python
from src.fields import DiffusionField, TerritoryField

# Scent trail field (diffuses + decays)
scent = DiffusionField(width, height, diffusion_rate=0.2, decay_rate=0.95)

# Walkers deposit scent
for walker in spawner.walkers:
    scent.deposit(walker.x, walker.y, walker.vigor * 0.5)

scent.update()  # Diffuse to neighbors + decay

# Territory tracking (emergent colors from visitor history)
territory = TerritoryField(width, height, chunk_size=8)
territory.claim(walker)  # Vigor-weighted ownership
```

#### 4. **Events: Temporal Perturbations**

```python
from src.events import EventScheduler, SpawnRateBurst, GlobalColorShift, AESTHETIC_POOL

scheduler = EventScheduler()
system = {'spawner': spawner, 'field': scent, 'config': {...}}

# Schedule specific event
event = SpawnRateBurst(duration=100, multiplier=2.0)
scheduler.add_event(event, delay=50)

# Spawn random event from pool
scheduler.spawn_random_event(AESTHETIC_POOL, delay_range=(0, 100))

# Update each tick
scheduler.update(system)  # Events modify system parameters
```

#### 5. **Complete Example: 50 Lines**

```python
from src.automata import Spawner, RandomWalk
from src.genetics import Genome
from src.fields import DiffusionField, TerritoryField
from src.events import EventScheduler, AESTHETIC_POOL

# Setup
spawner = Spawner(max_walkers=300, width=80, height=24)
scent = DiffusionField(80, 24)
territory = TerritoryField(80, 24, chunk_size=8)
events = EventScheduler()
behavior = RandomWalk(eight_way=True)

# Spawn initial population
for _ in range(20):
    spawner.spawn_random(genome=Genome(color_h=random.random()))

# Main loop
while True:
    # Walker actions
    for walker in spawner.walkers:
        scent.deposit(walker.x, walker.y, walker.vigor)
        territory.claim(walker)
        dx, dy = behavior.get_move(walker.x, walker.y)
        walker.move(dx, dy, 80, 24, wrap=True)

    # Reproduction
    if not spawner.is_full() and random.random() < 0.05:
        w1, w2 = random.sample(spawner.walkers, 2)
        spawner.spawn_from_parents(w1, w2)

    # Update fields
    scent.update()
    territory.update()

    # Update events
    events.update({'spawner': spawner, 'field': scent})

    # Render (composite fields + walkers)...
```

See `ARCHITECTURE.md` for detailed design patterns and `experiments/README.md` for more examples.

## Directional Glyph System

A probabilistic character selection system with **1,742 glyphs** for organic terminal animations.

The glyph system features:
- **Comprehensive Unicode coverage** - 11 ranges including arrows, clocks, braille, geometric shapes
- **Intelligent categorization** - Auto-inferred direction, intensity, and style tags
- **Probabilistic selection** - Same criteria, varied results every time!
- **Connection logic** - Proper NESW connector tracking for walkers
- **Perturbative events** - Dynamic intensity modulation (bursts, calms, waves)

### Database Coverage

The full database (`glyph_database_full.json`) includes:
- **Arrows** (112 glyphs) - Basic, supplemental, long, curved, double
- **Box Drawing** (128 glyphs) - Light, heavy, double connectors
- **Geometric Shapes** (96 glyphs) - Triangles, circles, polygons
- **Block Elements** (32 glyphs) - Partial blocks, density gradients
- **Braille Patterns** (256 glyphs) - Subtle directional hints
- **Clock Faces** (24 glyphs) - Hour hand directions (12, 1, 1:30, 2, etc.)
- **Symbols & Dingbats** (448+ glyphs) - Decorative and directional
- **646 additional glyphs** from misc symbols and fullwidth forms

### Quick Start

```bash
# Build comprehensive database (1,742 glyphs)
python3 tools/build_comprehensive_db.py --all-ranges -o glyph_database_full.json

# Run enhanced walker with proper connections + perturbative events
python3 demos/walker_enhanced.py --database glyph_database_full.json

# Watch intensity changes from events (shown in status line)
# Events include: Energy Burst, Calm Period, Heavy Wave, etc.

# Run without events (steady intensity)
python3 demos/walker_enhanced.py --no-events --base-intensity 0.7
```

### API Example

```python
from src.glyphs import GlyphPicker, Direction

# Load comprehensive database
picker = GlyphPicker.from_json("glyph_database_full.json")

# Get varied characters for same direction
char = picker.get(direction=Direction.E, intensity=0.7)  # Different each time!

# Filter by style
arrow = picker.get(direction=Direction.NE, style="arrow")
clock = picker.get(direction=Direction.SE, style="clock")
braille = picker.get(direction=Direction.S, style="braille", intensity=0.3)
```

See `src/glyphs/README.md` for full documentation.

## License
MIT — do whatever makes beautiful waves.


---

## New: Color Schemes, Blends & Duotone Layer

**Schemes** (`--color-scheme`): `complement, analogous, triad, tetrad, split, monochrome, warm, cool, rainbow, custom`  
**Blend spaces** (`--blend`): `hsv, hsl, rgb, oklab` (OKLab implemented inline; no deps)  
**Pairing** (`--pairing`): how the background color relates to the foreground — `opposite, adjacent, none`  
**Stops** (`--stops`): for `--color-scheme custom`, e.g. `--stops "#ff0088,#00ffaa,#223344"`  
**Gradient** (`--gradient`): `x` (across columns), `t` (over time), or `xt` (both). Tune with `--scale`.  
**Duotone layer** (`--layer-mode duotone`): uses upper half‑block `▀` so the **foreground ink** sits “on top” of a different **background color** in the same cell (overlay‑ish effect).

Examples:

```bash
# Triad palette blended in OKLab, complementary bg pairing, slow xt gradient
python3 ascii_waves.py --rows 240 --color-scheme triad --blend oklab --pairing opposite --gradient xt --scale 2.5

# Custom stops, HSL blend, adjacent bg pairing, duotone overlay (ignores connector shapes)
python3 ascii_waves.py --rows 200 --layer-mode duotone   --color-scheme custom --stops "#ffd1dc,#8ec5ff,#c7ffd8" --blend hsl --pairing adjacent

# Monochrome with darker bg, connectors intact
python3 ascii_waves.py --rows 220 --color-scheme monochrome --bg-gain -0.25 --style rounded
```
