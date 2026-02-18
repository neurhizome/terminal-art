# 📸 Pattern Museum

A collection of captured terminal screenshots showing beautiful emergent patterns.

## What is this?

Each `.ans` file in this directory contains a terminal screenshot with ANSI escape codes intact. When you `cat` the file, you see exactly what was on screen at the moment of capture - colors, characters, everything!

## Viewing Captures

```bash
# View a specific capture
cat museum/2026-02-18_153022_rainbow_spiral.ans

# Browse all captures
python3 -m src.capture

# Or
python3 src/capture.py
```

## Taking Captures

While running any sketchbook experiment:

**Press `c` to capture!**

The screenshot will be saved to `museum/` with metadata about:
- When it was captured
- Which script generated it
- Random seed (if set)
- Parameters at the time
- Tick number
- Your description

Example:
```bash
python3 -m sketches meditative
# See something cool?
# Press 'c' to capture!
# 📸 Saved: museum/2026-02-18_153515_capture_000.ans
```

## File Format

Each `.ans` file starts with metadata comments:

```
# CAPTURE: rainbow_spiral
# Date: 2026-02-18 15:30:22
# Script: sketchbook
# Seed: 42
# Params: walkers=250, mutation_rate=0.05, spawn_rate=0.1
# Tick: 1523
# Description: Perfect spiral formation!
#
# To view: cat museum/2026-02-18_153022_rainbow_spiral.ans
#

[ANSI escape codes with full terminal state...]
```

## Building Your Collection

As you explore, capture your favorite moments:

1. **Beautiful Gradients** - Smooth color transitions
2. **Emergent Patterns** - Unexpected structures
3. **Rare Events** - Unique configurations
4. **Evolution Snapshots** - Key moments in dynamics
5. **Aesthetic Highlights** - Pure visual beauty

## Tips

- **Capture Often** - You can always delete later
- **Note the Seed** - Reproduce interesting patterns
- **Describe It** - Future you will thank you
- **Share Favorites** - Show others cool finds
- **Build Narratives** - Capture time series of evolution

## Organization Ideas

You can organize captures however you like:

```bash
# By category
museum/gradients/
museum/spirals/
museum/chaos/
museum/favorites/

# By date
museum/2026-02-18/
museum/2026-02-19/

# By experiment
museum/speciation/
museum/predator_prey/
museum/gradient_flow/
```

## Gallery

Browse captures with:

```bash
python3 src/capture.py
```

Example output:
```
📸 Museum: 15 captures

======================================================================

Rainbow Spiral
  Date: 2026-02-18 15:30:22
  Perfect spiral formation with 5 arms!
  View: cat museum/2026-02-18_153022_rainbow_spiral.ans

Color Explosion
  Date: 2026-02-18 16:12:45
  Mutation burst created full spectrum
  View: cat museum/2026-02-18_161245_color_explosion.ans

...
```

## Sharing

ANSI files are pure text - they work great with git!

```bash
git add museum/*.ans
git commit -m "Add new pattern captures"
```

Others can view your captures with just `cat`.

## Start Capturing!

Run an experiment and press `c` when you see something cool:

```bash
python3 -m sketches aesthetic
# Press 'c' to capture screenshots
# Press 'q' to quit
```

Happy pattern hunting! 📸✨
