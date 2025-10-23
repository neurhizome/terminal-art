# Experiments

This directory contains **composable experiments** built from modular toolkit components.

Each experiment demonstrates different ways to combine:
- **Walkers** (`src.automata`) - Entities with position and genetics
- **Genomes** (`src.genetics`) - Heritable color traits with drift
- **Fields** (`src.fields`) - Spatial dynamics (diffusion, territory, energy)
- **Events** (`src.events`) - Temporal perturbations
- **Renderers** (`src.renderers`) - Display systems

## Quick Start

### Simple Walkers (30 lines)
Bare minimum: Just walkers moving around.

```bash
python3 experiments/simple_walkers.py --walkers 100 --delay 0.02
```

**Modules used:** `automata`, `genetics`

### Memetic Territories (100 lines)
Full-featured: Walkers + scent trails + territory + events.

```bash
# With events
python3 experiments/memetic_territories.py --initial-walkers 20 --max-walkers 300 --events

# Without events (stable)
python3 experiments/memetic_territories.py --initial-walkers 30 --max-walkers 500

# High spawn rate (chaotic)
python3 experiments/memetic_territories.py --spawn-rate 0.15 --events
```

**Modules used:** `automata`, `genetics`, `fields`, `events`, `renderers`

## Creating New Experiments

### Pattern 1: Minimal (Pure Walkers)

```python
from src.automata import Walker, Spawner, RandomWalk
from src.genetics import Genome

spawner = Spawner(max_walkers=100)
behavior = RandomWalk()

# Spawn walkers
for _ in range(50):
    spawner.spawn_random(genome=Genome(color_h=random.random()))

# Main loop
while True:
    for walker in spawner.walkers:
        dx, dy = behavior.get_move(walker.x, walker.y)
        walker.move(dx, dy, width, height)
    # render...
```

### Pattern 2: Field-Driven

```python
from src.fields import DiffusionField
from src.automata import GradientFollow

scent_field = DiffusionField(width, height)

# Walkers deposit and sense
for walker in spawner.walkers:
    scent_field.deposit(walker.x, walker.y, walker.vigor)
    behavior = GradientFollow('scent')
    dx, dy = behavior.get_move(walker.x, walker.y, field=scent_field)
    walker.move(dx, dy, width, height)

scent_field.update()  # Diffuse + decay
```

### Pattern 3: Event-Driven

```python
from src.events import EventScheduler, AESTHETIC_POOL

scheduler = EventScheduler()
system = {'spawner': spawner, 'config': {...}}

# Schedule events
scheduler.spawn_random_event(AESTHETIC_POOL)

# Update each tick
scheduler.update(system)  # Events modify system
```

## Experiment Ideas

### Easy
- **Color Speciation**: Walkers of different colors can't breed
- **Predator-Prey**: Two walker types with different behaviors
- **Seasonal Cycles**: Modulate spawn rate over time
- **Different Glyph Species**: Use glyph picker for walker chars

### Medium
- **Resource Fields**: Walkers consume field values to maintain vigor
- **Magnetic Attraction**: Walkers attracted to similar colors
- **Multi-Layer**: Separate foreground/background walker populations
- **Trail Visualization**: Render scent field as background heat

### Hard
- **3D Projection**: Use Unicode blocks for pseudo-3D
- **Evolutionary Tournaments**: Pit trait combinations against each other
- **Emergence Metrics**: Quantify pattern complexity over time
- **Rule Transitions**: Walkers can switch between different rule systems

## Module Reference

### `src.automata`
- `Walker` - Entity with position + genome
- `Spawner` - Population management
- `RandomWalk`, `LevyFlight`, `GradientFollow`, etc. - Movement behaviors

### `src.genetics`
- `Genome` - Memetic trait container (color, vigor, traits)
- `circular_mean`, `circular_distance` - Hue math

### `src.fields`
- `DiffusionField` - Spreading + decay
- `TerritoryField` - Chunked ownership with emergent colors

### `src.events`
- `EventScheduler` - Timing system
- `SpawnRateBurst`, `GlobalColorShift`, `VigorWave`, etc. - Event types
- `AESTHETIC_POOL`, `CHAOS_POOL`, etc. - Pre-built event collections

### `src.renderers`
- `TerminalStage` - Full-screen terminal canvas with double-buffering

## Tips

1. **Start simple**: Begin with just walkers, add complexity incrementally
2. **Hot-swap behaviors**: Change movement strategies without refactoring
3. **Compose fields**: Layer multiple field types for rich dynamics
4. **Event pools**: Use pre-built pools or create custom event mixes
5. **Profile first**: Add features, then optimize hot paths
6. **Status lines**: Display metrics for understanding emergent patterns

## Performance

- **Small experiments** (< 100 walkers, no fields): 60+ FPS
- **Medium** (100-500 walkers, 1-2 fields): 20-30 FPS
- **Large** (500+ walkers, multiple fields): 10-20 FPS
- **Mobile** (iOS/iSH): Reduce walker count, simplify rendering

Optimization tips:
- Use sparse field updates (only update dirty cells)
- Batch rendering operations
- Lower field diffusion rate
- Increase chunk size for territory fields
- Disable events for stable performance
