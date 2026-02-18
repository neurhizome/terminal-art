# Modular Experimentation Architecture

## Philosophy

Build **composable building blocks** for terminal automata experiments. Each module should:
- Work independently
- Compose cleanly with other modules
- Have clear inputs/outputs
- Follow single-responsibility principle

## Module Structure

```
src/
├── glyphs/          # Character selection (DONE)
│   ├── direction.py
│   ├── glyph_data.py
│   └── picker.py
├── renderers/       # Terminal rendering (DONE)
│   └── terminal_stage.py
├── automata/        # Walker/agent entities (NEW)
│   ├── walker.py         # Base walker class
│   ├── spawner.py        # Population management
│   └── behaviors.py      # Movement strategies
├── fields/          # Grid-based systems (NEW)
│   ├── base.py           # Abstract field interface
│   ├── diffusion.py      # Scent trails / chemical diffusion
│   ├── territory.py      # Chunked ownership tracking
│   └── energy.py         # Excitable medium
├── genetics/        # Memetic trait system (NEW)
│   ├── genome.py         # HSV color genomes
│   ├── inheritance.py    # Parent → child trait flow
│   └── speciation.py     # Reproductive barriers
├── events/          # Perturbative dynamics (NEW)
│   ├── event.py          # Base event class
│   ├── catalog.py        # Pre-built events library
│   └── scheduler.py      # Event timing/triggering
├── metrics/         # Emergence measurement (NEW)
│   ├── diversity.py      # Color/trait diversity
│   ├── patterns.py       # Spatial pattern detection
│   └── complexity.py     # Information-theoretic measures
└── utils/           # Shared helpers
    └── colors.py         # HSV/RGB conversion, circular mean
```

## Core Abstractions

### 1. Walker (src/automata/walker.py)

```python
class Walker:
    """Entity that moves through terminal space with genetic traits"""

    def __init__(self, x, y, genome):
        self.x, self.y = x, y
        self.genome = genome        # Genetic traits (color, vigor, etc.)
        self.age = 0
        self.vigor = 1.0

    def move(self, grid, behavior):
        """Update position using behavior strategy"""

    def interact(self, other_walker):
        """Reproduce, compete, or cooperate"""

    def deposit(self, field):
        """Leave scent trail or modify field"""

    def sense(self, field):
        """Read field values to inform behavior"""
```

**Key Design:**
- Walker is just **position + traits** - behavior is injected
- Interactions return new walkers (reproduction) or modify existing ones
- Walkers don't know about rendering - they output (x, y, char, color)

### 2. Field (src/fields/base.py)

```python
class Field(ABC):
    """2D grid that stores and updates values"""

    @abstractmethod
    def get(self, x, y):
        """Read value at position"""

    @abstractmethod
    def set(self, x, y, value):
        """Write value at position"""

    @abstractmethod
    def update(self):
        """Apply field dynamics (diffusion, decay, etc.)"""

    def render(self):
        """Return grid of (char, fg_color, bg_color) for display"""
```

**Field Types:**
- **DiffusionField** - Values spread to neighbors and decay
- **TerritoryField** - Tracks ownership history (weighted by vigor)
- **EnergyField** - Excitable medium with cascade dynamics
- **ConnectionField** - Maintains NESW bitmasks (what we built already!)

### 3. Genome (src/genetics/genome.py)

```python
class Genome:
    """Memetic trait container with inheritance rules"""

    def __init__(self, color_h=None, vigor=1.0, **traits):
        self.color_h = color_h or random.random()  # Hue [0, 1)
        self.vigor = vigor
        self.traits = traits  # Extensible trait dict

    def reproduce_with(self, other, mutation_rate=0.03):
        """Blend genomes with Gaussian drift"""
        child_h = circular_mean_hue(
            [self.color_h, other.color_h],
            [self.vigor, other.vigor]
        )
        child_h += random.gauss(0, mutation_rate)
        child_vigor = (self.vigor + other.vigor) / 2

        return Genome(color_h=child_h, vigor=child_vigor)

    def distance_to(self, other):
        """Circular hue distance for speciation checks"""
        delta = abs(self.color_h - other.color_h)
        return min(delta, 1.0 - delta)
```

**Key Features:**
- Colors are primary genetic marker (visible phenotype)
- Vigor affects inheritance weighting (dominant traits)
- Extensible traits dict for custom properties
- Distance metric enables reproductive barriers

### 4. Event (src/events/event.py)

```python
class Event:
    """Perturbative dynamics that modulate system parameters"""

    def __init__(self, duration, strength, target_param):
        self.duration = duration
        self.strength = strength
        self.target_param = target_param
        self.elapsed = 0

    def apply(self, system):
        """Modify system parameters"""

    def is_finished(self):
        return self.elapsed >= self.duration
```

**Event Examples:**
- **IntensityBurst** - Increase spawn rate temporarily
- **ColorShift** - Global hue rotation
- **VigorWave** - Modulate competitive strength
- **Extinction** - Remove low-fitness walkers

### 5. Experiment Composer

```python
# experiments/memetic_territories.py

from src.automata import Walker, Spawner
from src.fields import DiffusionField, TerritoryField
from src.genetics import Genome
from src.events import EventScheduler, IntensityBurst
from src.renderers import TerminalStage

# Compose modular components
stage = TerminalStage()
spawner = Spawner(max_walkers=500)
scent_field = DiffusionField(stage.width, stage.height, decay=0.95)
territory_field = TerritoryField(stage.width, stage.height, chunk_size=8)
events = EventScheduler()

# Seed initial population
for _ in range(10):
    genome = Genome(color_h=random.random(), vigor=random.uniform(0.5, 1.5))
    walker = Walker(random.randint(0, stage.width),
                    random.randint(0, stage.height),
                    genome)
    spawner.add(walker)

# Main loop
while True:
    events.update()  # Trigger scheduled events

    for walker in spawner.walkers:
        walker.deposit(scent_field)        # Leave trail
        walker.sense(scent_field)          # Read environment
        walker.move(grid, behavior)        # Update position
        territory_field.claim(walker)      # Mark ownership

    scent_field.update()      # Diffuse + decay
    territory_field.update()  # Blend ownership

    # Render composite
    stage.render_field(territory_field)  # Background
    stage.render_walkers(spawner.walkers)  # Foreground
    stage.flush()
```

## Design Principles

### 1. **Separation of Concerns**
- Walkers handle movement/genetics
- Fields handle spatial dynamics
- Renderers handle display
- Events handle temporal perturbations

### 2. **Dependency Injection**
```python
# Good: Behavior is injected
walker.move(grid, behavior=RandomWalk())
walker.move(grid, behavior=GradientFollow(field))

# Bad: Behavior is hardcoded
walker.move()  # Has to know how to move
```

### 3. **Data Pipelines**
```
Walkers → deposit() → Fields → update() → render() → Stage → Display
   ↑                                         ↓
   └──────────── sense() ←──────────────────┘
```

### 4. **Hot-Swappable Components**
```python
# Switch rendering strategies
stage.set_renderer(TerritoryRenderer())
stage.set_renderer(HeatmapRenderer())
stage.set_renderer(GlyphRenderer())

# Switch movement behaviors
walkers = [Walker(..., behavior=RandomWalk()) for _ in range(100)]
walkers = [Walker(..., behavior=Chemotaxis(scent_field)) for _ in range(100)]
```

## Usage Patterns

### Pattern 1: Pure Walkers (No Fields)
```python
# Just moving entities with genetics
spawner = Spawner()
for walker in spawner.walkers:
    walker.move(behavior=LevyFlight())
    if walker.collides_with(other):
        child = walker.reproduce_with(other)
        spawner.add(child)
```

### Pattern 2: Field-Driven Dynamics
```python
# Walkers react to field gradients
energy_field = EnergyField(w, h)
for walker in spawner.walkers:
    gradient = energy_field.gradient_at(walker.x, walker.y)
    walker.move(behavior=GradientFollow(gradient))
    walker.deposit(energy_field)
```

### Pattern 3: Multi-Field Composition
```python
# Multiple overlapping fields
scent = DiffusionField(w, h, decay=0.95)
territory = TerritoryField(w, h, chunk_size=8)
energy = EnergyField(w, h)

# Walkers sense all fields
for walker in spawner.walkers:
    walker.sense([scent, territory, energy])
    walker.decide_action()  # Uses sensory input
```

## Next Steps

1. **Implement Core Modules** (walker, field, genome)
2. **Create Example Experiments** showing composition
3. **Build Experiment Template** for quick starts
4. **Document Patterns** with real examples
5. **Performance Profiling** for large populations

## Success Metrics

A good modular system means:
- New experiment in < 50 lines
- Swap components without refactoring
- Reuse 80%+ of code across experiments
- Clear boundaries between modules
- Easy to test in isolation
