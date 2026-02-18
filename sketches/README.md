# Sketchbook System - Quick Creative Experiments

This directory is for **rapid prototyping** and **creative exploration**.

## Philosophy

- **Speed > Perfection** - Get ideas running in minutes
- **Experiment Freely** - No pressure to be production-ready
- **Document Discovery** - Note cool patterns you find
- **Share Favorites** - Show what emerges

## Quick Start

```python
# sketches/my_idea.py
from src.sketchbook import quick_sketch

# Minimal setup
sketch = quick_sketch(
    walkers=200,
    colors='rainbow',
    behavior='random',
    fields=['diffusion', 'territory']
)

# Optional: customize
sketch.spawn_rate = 0.1
sketch.mutation_rate = 0.05
sketch.add_event('color_shift', interval=200)

# Run!
sketch.run()
```

## Presets

Start with a vibe and modify:

```bash
# Calm and meditative
python3 -m sketches.preset meditative

# High energy chaos
python3 -m sketches.preset chaotic

# Competitive dynamics
python3 -m sketches.preset competitive

# Pure aesthetic beauty
python3 -m sketches.preset aesthetic
```

## Interactive Controls

While running:
- `Space` - Pause/unpause
- `+/-` - Adjust spawn rate
- `m/M` - Change mutation rate
- `e` - Trigger random event
- `s` - Save seed/config
- `r` - Reset
- `c` - Screenshot
- `q` - Quit

## Discovery Log

Found something cool? Document it!

```bash
# Save current state
Press 's' during run → saves to discoveries/YYYY-MM-DD_HHMMSS.json

# Replay later
python3 -m sketches.replay discoveries/2026-02-18_143022.json
```

## Examples

### Example 1: Magnetic Colors
Walkers attracted to similar hues, repelled by different ones.

```python
from src.sketchbook import quick_sketch

s = quick_sketch(walkers=250, colors='rainbow')
s.attraction_field(threshold=0.2, strength=0.4)  # Attract within 0.2 hue distance
s.run()
```

### Example 2: Color Cascade
High mutation creates rainbow waterfalls.

```python
from src.sketchbook import quick_sketch

s = quick_sketch(walkers=300, behavior='levy_flight')
s.mutation_rate = 0.15
s.spawn_rate = 0.2
s.fields = ['diffusion']
s.run(preset='flow')
```

### Example 3: Territorial Wars
Multiple starting species battle for space.

```python
from src.sketchbook import quick_sketch

s = quick_sketch(walkers=400)
s.seed_species(n=6, colors='evenly_spaced')
s.breeding_threshold = 0.15  # Strict barriers
s.fields = ['territory']
s.run()
```

## Tips for Discovery

1. **Start Simple** - Add one feature at a time
2. **Watch Patterns** - Let it run for 1000+ ticks
3. **Note Surprises** - Unexpected behavior is gold
4. **Save Seeds** - Reproduce interesting patterns
5. **Iterate Fast** - Change one param, see what happens
6. **Combine Mechanics** - Mix different modules

## Contributing Your Sketches

Found something awesome? Add it!

1. Save to `sketches/your_idea.py`
2. Add screenshot to `gallery/`
3. Document in `discoveries/PATTERNS.md`
4. Share parameters that worked

## Gallery Favorites

See `gallery/README.md` for visual showcase of beautiful patterns.
