# Mobile Optimization Guide

## Problem: Blank Screen / Broken Display

The comprehensive database (`glyph_database_full.json` with 1,742 glyphs) included:
- **Emoji** (🕐🕜🕑) - 2 cells wide, breaks cursor positioning
- **Fullwidth characters** (ｆｕｌｌｗｉｄｔｈ) - 2 cells wide
- **CJK characters** - variable width

These cause the walker to misalign and produce a "blank" or garbled screen.

## Solution: Optimized Database

We created `glyph_database_optimized.json` (720 glyphs):
- **All single-width** (wcwidth == 1)
- **No emoji** - filtered out
- **No fullwidth** - removed Halfwidth/Fullwidth Forms range
- **41% smaller** - faster loading on mobile

### Comparison

| Database | Glyphs | Size | Wide Chars | Mobile-Safe |
|----------|--------|------|------------|-------------|
| `glyph_database.json` | 43 | 9.5 KB | ❌ None | ✅ Yes |
| `glyph_database_full.json` | 1,742 | 342 KB | ⚠️ Many | ❌ No |
| `glyph_database_optimized.json` | 720 | ~90 KB | ❌ None | ✅ Yes |

## Usage

### Build Optimized Database

```bash
python3 tools/build_optimized_db.py -o glyph_database_optimized.json -v
```

### Use Mobile-Optimized Walker

```bash
# Recommended for mobile/constrained environments
python3 demos/walker_mobile.py --database glyph_database_optimized.json

# Simple mode (no status line, faster)
python3 demos/walker_mobile.py --simple --no-color

# Specific style
python3 demos/walker_mobile.py --style connector --intensity 0.7
```

## What Got Filtered Out

### Removed Ranges
- ❌ **Misc Symbols** (U+2600-U+26FF) - Mostly emoji
- ❌ **Braille** (U+2800-U+28FF) - 256 glyphs, mostly non-directional
- ❌ **Halfwidth/Fullwidth** (U+FF00-U+FFEF) - All wide!
- ❌ **Dingbats** (U+2700-U+27BF) - Some are wide
- ❌ **Emoji ranges** (U+1F300-U+1F9FF)

### Kept Ranges (All Single-Width)
- ✅ **Arrows** (U+2190-U+21FF) - 112 glyphs
- ✅ **Box Drawing** (U+2500-U+257F) - 128 glyphs
- ✅ **Block Elements** (U+2580-U+259F) - 29 glyphs
- ✅ **Geometric Shapes** (U+25A0-U+25FF) - 87 glyphs
- ✅ **Supplemental Arrows A** (U+27F0-U+27FF) - 16 glyphs
- ✅ **Supplemental Arrows B** (U+2900-U+297F) - 126 glyphs
- ✅ **Misc Symbols & Arrows** (U+2B00-U+2BFF) - 198 glyphs

## Performance Tips

1. **Use `--simple` mode** - Disables status line, reduces rendering
2. **Use `--no-color`** - Faster on constrained terminals
3. **Lower `--batch` size** - Smoother animation (default: 100)
4. **Use `--wrap`** - Avoids boundary calculations

```bash
# Maximum performance for mobile
python3 demos/walker_mobile.py --simple --no-color --batch 50
```

## Troubleshooting

**Still seeing broken display?**
- Make sure you're using `glyph_database_optimized.json`
- Try `--simple --no-color` flags
- Check your terminal supports UTF-8: `echo $LANG`
- Verify terminal size: `tput cols && tput lines`

**Want even fewer glyphs?**
Edit `tools/build_optimized_db.py` and remove ranges you don't need.
