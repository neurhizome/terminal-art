# terminal-art — Modular Terminal Graphics & Unicode Automata Toolkit

A lightweight toolkit for creating animated terminal graphics using Unicode characters,
cellular automata, and directional walkers. Most demos are **dependency-free** and run
on any POSIX terminal, including **iSH on iOS**.

## Features

- **Directional Walkers** - Create flowing, organic animations with NESW connector logic
- **Unicode Glyph System** - Scan and categorize thousands of Unicode characters
- **Terminal Stage** - Efficient full-screen rendering with double-buffering and 24-bit color
- **Modular Design** - Clean separation between core library and demos
- **Cellular Automata** - Multiple CA-driven renderers with customizable rules

## Project Structure

```
terminal-art/
├── src/              # Core library code
│   ├── renderers/    # Terminal rendering engines (TerminalStage, etc.)
│   ├── glyphs/       # Character mapping and selection system
│   └── utils/        # Shared utilities and helpers
├── demos/            # Runnable example scripts
│   ├── walker_*.py   # Walker-based animations
│   ├── braille_*.py  # Braille pattern demos
│   └── ascii_*.py    # ASCII/box-drawing demos
├── tools/            # Utilities for glyph discovery
│   ├── unicode_scanner.py  # Scan Unicode ranges
│   └── glyph_viewer.py     # Browse glyph collections
├── scripts/          # Bootstrap and setup scripts
└── tests/            # Future test suite
```

## Quick Start

### 1. Set up virtual environment (recommended)

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Try some demos

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

## Directional Glyph System

**NEW!** A probabilistic character selection system for more organic terminal animations.

Instead of static character maps, the glyph system:
- **Categorizes** Unicode chars by direction, intensity, and style
- **Selects probabilistically** - same criteria, varied results!
- **Enables organic walkers** - encode both direction AND intensity

```python
from src.glyphs import GlyphPicker, Direction

picker = GlyphPicker.from_json("glyph_database.json")
char = picker.get(direction=Direction.E, intensity=0.7)  # Varies each call!
```

**Try it:**
```bash
# Generate starter database (arrows + box-drawing)
python3 tools/glyph_categorizer.py --quick-start

# Run probabilistic walker demo
python3 demos/walker_probabilistic.py --style connector

# Try with arrows
python3 demos/walker_probabilistic.py --style arrow --intensity-base 0.7
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
