# terminal-art (asciicology) — Modular Terminal Automata Toolkit

A **composable toolkit** for running emergence experiments in the terminal, and a **living research blog** documenting what those experiments produce.

The toolkit provides building blocks — walkers with genetic traits, diffusion fields, event perturbations, a probabilistic glyph system — that compose to investigate questions that don't have predetermined answers. *Why do boundaries sharpen?* *What does the Pythagorean comma look like as a population dynamic?* *Can speciation fail before the first tick?*

The blog at `docs/` records what the experiments actually do, which is rarely what was predicted. Sessions are not tutorials. They are evidence that certain behaviors are possible.

Most components are **dependency-free** and run on any POSIX terminal, including **iSH on iOS**.

---

## The Blog

Session posts live in `docs/_posts/`. Each documents an experiment run, what was observed, and what remains open.

Sessions this week:

| | Session | Discovery |
|--|---------|-----------|
| [001](docs/_posts/2026-02-19-session-001-the-sharpening.md) | **The Sharpening** | Boundaries emerge at diffusion=0.15 without anyone drawing them; the seam is maintained by mutual pressure |
| [002](docs/_posts/2026-02-19-session-002-the-event-horizon.md) | **The Event Horizon** | Field inertia outlasts the agents who created it; territory remembers |
| [003](docs/_posts/2026-02-20-session-003-the-seam-strike.md) | **The Seam Strike** | Destroying a seam produces no man's land, not a new seam |
| [004](docs/_posts/2026-02-20-session-004-the-dissolution.md) | **The Dissolution** | Eight species collapse to one when breed\_threshold > species spacing; the math was against divergence before tick 0 |
| [005a](docs/_posts/2026-02-21-session-005-wolf-interval.md) | **Wolf Interval** | The circle of fifths draws itself via stigmergy; the wolf gap appears with no rule placing it |
| [005b](docs/_posts/2026-02-21-session-005-mathematical-forms.md) | **Mathematical Forms** | Mandelbrot, Recamán, Lissajous in ASCII; mathematical objects have feelings that survive translation |

The **knowledge graph** at `/graph/` renders the topology of what-has-influenced-what. It rebuilds itself on every commit that touches a post or concept — the same stigmergic principle the simulations use, applied to the documentation. Run manually: `python3 tools/graph_viz.py`.

The **quest board** at `docs/quests.md` tracks things the simulation can't produce: images, music, words. Human returns go in `human/returns/` and are incorporated on the next cycle.

---

## Core Modules

- **Genetics** (`src.genetics`) — Memetic color genomes with inheritance and drift
- **Automata** (`src.automata`) — Walker entities with pluggable behaviors
- **Fields** (`src.fields`) — Diffusion, territory tracking, energy grids
- **Events** (`src.events`) — Perturbative dynamics for temporal variation
- **Renderers** (`src.renderers`) — Terminal Stage with double-buffering
- **Glyphs** (`src.glyphs`) — Probabilistic character selection (1,742 glyphs)

### Design principles

- **Modular composition** — mix and match components to build experiments
- **Dependency injection** — behaviors are passed in, not inherited
- **Colors as memes** — HSV traits flow through populations via reproduction
- **Emergence over programming** — simple rules, complex patterns; the gap between almost-right and right is often where the behavior lives

---

## Project Structure

```
terminal-art/
├── src/                          # Core modular toolkit (~3,073 LOC)
│   ├── automata/                 # Walker entities + population management + behaviors
│   ├── genetics/                 # Memetic color genome with inheritance and drift
│   ├── fields/                   # Diffusion, territory, energy, connection fields
│   ├── events/                   # Event system + catalog (AESTHETIC_POOL, CHAOS_POOL)
│   ├── glyphs/                   # Probabilistic glyph selection (1,742 glyphs)
│   ├── renderers/                # TerminalStage: double-buffered full-screen canvas
│   └── utils/                    # Color math (HSV↔RGB, circular hue mean)
├── experiments/                  # Composable experiment scripts
│   ├── simple_walkers.py         # Minimal (30 lines): walkers + colors
│   ├── memetic_territories.py    # Full-featured: genetics + fields + events
│   ├── color_speciation.py       # Reproductive barriers and genetic dissolution
│   ├── gradient_flow.py          # Aesthetic mode: flowing color gradients
│   ├── predator_prey.py          # Lotka-Volterra dynamics
│   ├── wolf_interval.py          # Pythagorean comma drift + wolf gap emergence
│   ├── cipher_space.py           # Negative space: Lissajous curves erasing texture
│   └── README.md                 # Experiment composition guide
├── demos/                        # Standalone pre-modular demonstration scripts (20+)
│   ├── ascii_waves.py            # Cellular automata waves (most feature-rich demo)
│   ├── mandelbrot_ascii.py       # Mandelbrot set in Unicode density gradients
│   ├── recaman_arcs.py           # Recamán sequence as semicircular arcs
│   └── ...                       # braille, walker, morphing connector demos
├── docs/                         # Jekyll blog: posts, concepts, knowledge graph, quests
│   ├── _posts/                   # Session exploration blog posts
│   ├── concepts/                 # stigmergy.md, diffusion-memory.md
│   ├── assets/captures/          # ANSI art files + knowledge-graph.ans
│   └── quests.md                 # Human collaboration board
├── tools/                        # Glyph database builders + knowledge graph renderer
├── museum/                       # Captured ANSI animation outputs
├── scripts/
│   ├── hooks/post-commit         # Tracked copy of knowledge graph hook
│   └── speciation_capture.py     # Records animations to ANSI format
└── .github/workflows/pages.yml   # Jekyll deploy (runs graph_viz.py before build)
```

---

## Quick Start

### 1. Set up environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt   # just wcwidth
```

### 2. Run modular experiments

**Minimal — walkers + colors (30 lines):**
```bash
python3 experiments/simple_walkers.py --walkers 100
```

**Memetic territories — genetics + fields + events:**
```bash
python3 experiments/memetic_territories.py --initial-walkers 20 --max-walkers 300 --events
```

**Predator-prey dynamics (Lotka-Volterra):**
```bash
python3 experiments/predator_prey.py
```

**Pythagorean comma drift — watch the wolf gap emerge:**
```bash
python3 experiments/wolf_interval.py --walkers 200 --seed 17
```

**Negative space — Lissajous curves erasing texture fog:**
```bash
python3 experiments/cipher_space.py --ratios 3:2
```

**Color speciation — eight species, one survives:**
```bash
python3 experiments/color_speciation.py
```

See `experiments/README.md` for more examples and parameter documentation.

### 3. Run standalone demos

**Cellular automata waves:**
```bash
python3 demos/ascii_waves.py --rows 200 --delay 0.01 --style heavy --bg-glyph "·"
```

**Mandelbrot set in Unicode density gradients:**
```bash
python3 demos/mandelbrot_ascii.py --zoom-to -0.7269,0.1889
```

**Recamán sequence as arcs:**
```bash
python3 demos/recaman_arcs.py
```

**Animated connector walker:**
```bash
python3 demos/walker_connect_color16.py --style heavy --wrap
```

### 4. Scan Unicode for glyphs

```bash
python3 tools/unicode_scanner.py --start 0x2500 --end 0x259F --outfile box_drawing.json
```

---

## iSH Setup (Alpine iOS) — Truecolor & UTF‑8

```bash
apk update
apk add python3 py3-pip ncurses git
python3 -m venv venv
source venv/bin/activate
export TERM=xterm-256color
export COLORTERM=truecolor
export PYTHONIOENCODING=utf-8
pip install wcwidth
python3 demos/ascii_waves.py --rows 300 --delay 0.015 --style light --bg-set dots
```

> **Tip:** Use `glyph_database_optimized.json` (720 glyphs) on iOS for better performance.

---

## Modular Toolkit API

### Building Experiments from Components

Create custom automata experiments by composing modular building blocks:

#### 1. **Walkers with Genetic Traits**

```python
from src.automata import Walker, Spawner
from src.genetics import Genome

spawner = Spawner(max_walkers=500, width=80, height=24)
genome = Genome(color_h=0.5, vigor=1.2)  # Hue=cyan, high fitness
walker = Walker(x=40, y=12, genome=genome)
spawner.add(walker)

partner = spawner.walkers[0]
if walker.can_breed_with(partner):
    child = spawner.spawn_from_parents(walker, partner, mutation_rate=0.03)
```

#### 2. **Pluggable Movement Behaviors**

```python
from src.automata.behaviors import RandomWalk, GradientFollow, LevyFlight
from src.automata.behaviors import FifthSeek, RecamanWalk, LissajousOrbit

# Inject behavior (not inherited)
behavior = RandomWalk(eight_way=True)
dx, dy = behavior.get_move(walker.x, walker.y)
walker.move(dx, dy, width, height, wrap=True)

# Gradient following (attraction=False to flee instead of follow)
behavior = GradientFollow('scent', attraction=True)
dx, dy = behavior.get_move(walker.x, walker.y, field=scent_field)

# Seek nearest Pythagorean fifth in hue space
behavior = FifthSeek()
dx, dy = behavior.get_move(walker.x, walker.y, walkers=spawner.walkers)

# Step sizes follow the Recamán sequence
behavior = RecamanWalk()
dx, dy = behavior.get_move(walker.x, walker.y)

# Deterministic Lissajous parametric curve
behavior = LissajousOrbit(ratio_x=3, ratio_y=2, phase=0.0)
dx, dy = behavior.get_move(walker.x, walker.y, t=tick)
```

#### 3. **Fields: Diffusion, Territory, Energy**

```python
from src.fields import DiffusionField, TerritoryField

scent = DiffusionField(width, height, diffusion_rate=0.2, decay_rate=0.95)

for walker in spawner.walkers:
    scent.deposit(walker.x, walker.y, walker.vigor * 0.5)

scent.update()  # diffuse to neighbors + decay

territory = TerritoryField(width, height, chunk_size=8)
territory.claim(walker)  # vigor-weighted ownership
```

#### 4. **Events: Temporal Perturbations**

```python
from src.events import EventScheduler, SpawnRateBurst, GlobalColorShift
from src.events import EqualTemperament, AESTHETIC_POOL

scheduler = EventScheduler()
system = {'spawner': spawner, 'field': scent, 'config': {...}}

event = SpawnRateBurst(duration=100, multiplier=2.0)
scheduler.add_event(event, delay=50)

# Snap all walker hues to nearest semitone (equal temperament)
scheduler.add_event(EqualTemperament(), delay=500)

scheduler.spawn_random_event(AESTHETIC_POOL, delay_range=(0, 100))
scheduler.update(system)
```

#### 5. **Genome: Tuning and Drift**

```python
from src.genetics import Genome
import math

PYTHAGOREAN_FIFTH = math.log2(1.5)  # ≈ 0.58496

genome = Genome(color_h=0.3, vigor=1.0)

# Nudge hue toward Pythagorean fifth above a partner's hue
genome.tune_toward(partner_genome, rate=0.0008)

# Reproduce with circular hue drift
child_genome = genome.reproduce_with(partner_genome, mutation_rate=0.03)

# Reproductive compatibility check
dist = genome.distance_to(partner_genome)  # circular hue distance [0, 0.5]
```

#### 6. **Complete Example: ~50 Lines**

```python
from src.automata import Spawner, RandomWalk
from src.genetics import Genome
from src.fields import DiffusionField, TerritoryField
from src.events import EventScheduler, AESTHETIC_POOL

spawner = Spawner(max_walkers=300, width=80, height=24)
scent = DiffusionField(80, 24)
territory = TerritoryField(80, 24, chunk_size=8)
events = EventScheduler()
behavior = RandomWalk(eight_way=True)

for _ in range(20):
    spawner.spawn_random(genome=Genome(color_h=random.random()))

while True:
    for walker in spawner.walkers:
        scent.deposit(walker.x, walker.y, walker.vigor)
        territory.claim(walker)
        dx, dy = behavior.get_move(walker.x, walker.y)
        walker.move(dx, dy, 80, 24, wrap=True)

    if not spawner.is_full() and random.random() < 0.05:
        w1, w2 = random.sample(spawner.walkers, 2)
        spawner.spawn_from_parents(w1, w2)

    scent.update()
    territory.update()
    events.update({'spawner': spawner, 'field': scent})
    # render...
```

See `ARCHITECTURE.md` for design patterns and `experiments/README.md` for more examples.

---

## Directional Glyph System

Probabilistic Unicode character selection across 1,742 glyphs.

```python
from src.glyphs import GlyphPicker, Direction

picker = GlyphPicker.from_json("glyph_database_full.json")
char   = picker.get(direction=Direction.E, intensity=0.7)   # varies each call
arrow  = picker.get(direction=Direction.NE, style="arrow")
braille = picker.get(direction=Direction.S, style="braille", intensity=0.3)
```

**Database files:** `glyph_database.json` (essential), `glyph_database_optimized.json` (720, mobile), `glyph_database_full.json` (1,742, all ranges).

### Database Coverage

The full database includes:
- **Arrows** (112 glyphs) — basic, supplemental, long, curved, double
- **Box Drawing** (128 glyphs) — light, heavy, double connectors
- **Geometric Shapes** (96 glyphs) — triangles, circles, polygons
- **Block Elements** (32 glyphs) — partial blocks, density gradients
- **Braille Patterns** (256 glyphs) — subtle directional hints
- **Clock Faces** (24 glyphs) — hour hand directions
- **Symbols & Dingbats** (448+ glyphs) — decorative and directional
- **646 additional glyphs** from misc symbols and fullwidth forms

### Building Databases

```bash
python3 tools/build_comprehensive_db.py --all-ranges -o glyph_database_full.json
python3 tools/build_optimized_db.py -o glyph_database_optimized.json
python3 tools/unicode_scanner.py --start 0x2500 --end 0x259F --outfile box_drawing.json
```

See `src/glyphs/README.md` for full documentation.

---

## `ascii_waves.py` CLI

```bash
python3 demos/ascii_waves.py -h
```

Key options:
- `--style`: `light | heavy | double | rounded | ascii`
- `--bg-glyph` or `--bg-set`: background glyph(s) when CA bit is 0
- `--fg-glyph`: force a single glyph for CA bit 1
- `--extras` + `--extra-prob`: sprinkle from a glyph set (`dots,angles,blocks,braille-lite`)
- `--rule`, `--burst`, `--jitter`, `--rows`, `--delay`, `--seed`
- `--no-color`: disable ANSI colors
- `--color-scheme`: `complement | analogous | triad | tetrad | monochrome | warm | cool | rainbow | custom`
- `--blend`: `hsv | hsl | rgb | oklab`
- `--pairing`: how background relates to foreground — `opposite | adjacent | none`
- `--gradient`: `x` (columns), `t` (time), or `xt` (both)
- `--layer-mode duotone`: upper half-block `▀` with foreground ink over a different background color

Examples:

```bash
# Triad palette, OKLab blend, complementary bg, slow xt gradient
python3 demos/ascii_waves.py --rows 240 --color-scheme triad --blend oklab --pairing opposite --gradient xt --scale 2.5

# Monochrome with darker bg, connectors intact
python3 demos/ascii_waves.py --rows 220 --color-scheme monochrome --bg-gain -0.25 --style rounded
```

---

## License
MIT — do whatever makes beautiful waves.
