## Directional Glyph Mapping System

A probabilistic character selection system for terminal-based animations.

### Concept

Instead of using static character maps (like `TILES[Direction.E] = "─"`), this system:

1. **Categorizes** Unicode characters by visual properties:
   - **Direction** - Which way the character points/flows (N/E/S/W, or combinations)
   - **Intensity** - Visual weight from 0.0 (lightest) to 1.0 (heaviest)
   - **Style** - Tags like "arrow", "connector", "organic", "geometric"
   - **Weight** - Categorical: "light", "medium", "heavy"

2. **Selects probabilistically** - When you request a character, it:
   - Filters by your criteria
   - Weights matches by how well they fit
   - Returns a random selection (more natural variation!)

3. **Enables organic walkers** - Walkers can encode both direction AND intensity:
   ```python
   # Traditional: static mapping
   char = TILES[direction]  # Always the same!

   # New system: probabilistic selection
   char = picker.get(direction=E, intensity=0.7)  # Varies each time!
   ```

### Quick Start

```python
from src.glyphs import GlyphPicker, Direction

# Load database
picker = GlyphPicker.from_json("glyph_database.json")

# Get characters by criteria
char = picker.get(direction=Direction.E, intensity=0.7)
char = picker.get(direction=Direction.NE, style="arrow")
char = picker.get(direction=Direction.N, weight="light")

# Get all matches (not just random one)
glyphs = picker.get_all(direction=Direction.E, intensity_range=(0.5, 1.0))
```

### Building the Database

```bash
# Quick-start with arrows and box-drawing
python3 tools/glyph_categorizer.py --quick-start

# Scan a Unicode range to see characters
python3 tools/glyph_categorizer.py --scan 0x2500-0x259F
```

### File Structure

- `direction.py` - Direction constants and utilities
- `glyph_data.py` - GlyphInfo data class
- `picker.py` - Probabilistic selection engine
- `__init__.py` - Public API exports

### Database Format

```json
{
  "glyphs": [
    {
      "char": "→",
      "codepoint": "U+2192",
      "directions": "E",
      "intensity": 0.7,
      "styles": ["arrow", "geometric"],
      "weight": "medium"
    }
  ]
}
```

### Future Expansion

The starter database includes ~43 glyphs. You can expand it with:

- More arrow variations (curved, dashed, etc.)
- Braille patterns (subtle directional hints)
- Block characters (varying densities)
- Custom symbols from Nerd Fonts
- Geometric shapes
- Organic/flowing characters

Just add entries to the JSON or use the categorizer tool!
