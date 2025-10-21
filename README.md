# asciiwaves — Modular ASCII/Braille/Unicode Automata Renderer

A lightweight, dependency‑free toolkit to render cellular‑automata‑driven
“maze/river” flows using swappable **glyph sets**, **connector styles**, and **background
fill glyphs** — with optional 24‑bit color and multi‑char tiles.

It’s designed to play nicely in **iSH on iOS** as well as regular terminals.

## Why
- Swap foreground/background glyphs on the fly.
- Use Unicode sets: box‑drawing, blocks, braille, light/shade, angles, dots, ASCII density, etc.
- Keep the connector‑logic (N/E/S/W masks) from `maze_river.py`, but make it modular.
- Animate with simple 1D→2D CA rules (e.g., Rule 110), with “burst” spice and color jitter.

## Quick Start (any POSIX terminal)
```bash
python3 ascii_waves.py --rows 200 --delay 0.01 --style heavy --bg-glyph "·" --extras dots --extra-prob 0.07
```
Try a braille vibe as background:
```bash
python3 ascii_waves.py --bg-set braille-lite --style rounded --rows 300 --delay 0.02
```

Force a single foreground glyph for the “on” cells (ignoring connector boxes):
```bash
python3 ascii_waves.py --fg-glyph "╳" --bg-set shade --rows 200
```

Turn off color entirely:
```bash
python3 ascii_waves.py --no-color --style double --bg-glyph "░" --rows 120
```

## iSH Setup (Alpine) — Truecolor & UTF‑8
In iSH (iOS):
```bash
apk update
apk add python3 py3-pip ncurses
python3 -m ensurepip --upgrade
pip3 install --upgrade pip
# (No deps required for asciiwaves)
export TERM=xterm-256color
export COLORTERM=truecolor
export PYTHONIOENCODING=utf-8
```

Run a demo:
```bash
python3 /mnt/data/asciiwaves/ascii_waves.py --rows 300 --delay 0.015 --style light --bg-set dots
```

> Tip: iSH inherits iOS font rendering. For best alignment, prefer monospaced fonts that include box‑drawing & braille.
If a glyph looks off, switch to a different set (e.g., `--bg-set ascii-density`).

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

## Integrating With `maze_river.py`
`ascii_waves.py` carries over the connector logic and CA dynamics so you can use it standalone.
If you want to call into your existing script’s logic, treat it as a generator of bit‑rows and pass
those into `AsciiRenderer.render_row(bits)` (see code comments).

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
