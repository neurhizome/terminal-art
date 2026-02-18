#!/usr/bin/env python3
"""
Build an OPTIMIZED glyph database for mobile/constrained environments.

Filters out:
- Wide characters (fullwidth/halfwidth - break cursor positioning)
- Emoji (2 cells wide - misalign grid)
- Characters with wcwidth != 1
- Private Use Area that aren't properly single-width

Optimizations:
- Smaller database size for faster loading
- Only single-cell-width characters
- Focus on most useful ranges
"""
import argparse
import json
import sys
import unicodedata
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.glyphs import GlyphInfo, Direction, GlyphPicker
from src.glyphs.direction import string_to_direction
from tools.unicode_ranges import RANGES, SPECIAL_DIRECTIONAL

try:
    from wcwidth import wcwidth
except ImportError:
    def wcwidth(c):
        cat = unicodedata.category(c)
        return 0 if cat[0] in ('C', 'Z') or unicodedata.combining(c) else 1


def is_single_width(char: str) -> bool:
    """Check if character is exactly 1 cell wide."""
    try:
        w = wcwidth(char)
        return w == 1
    except:
        return False


def is_emoji_or_wide(char: str, codepoint: int) -> bool:
    """Detect emoji and wide characters that break alignment."""
    # Emoji ranges
    if 0x1F300 <= codepoint <= 0x1F9FF:  # Emoji & symbols
        return True
    if 0x2600 <= codepoint <= 0x26FF:  # Misc symbols (includes some emoji)
        # But keep the non-emoji ones - check by name
        try:
            name = unicodedata.name(char)
            if any(x in name for x in ['CLOCK', 'ARROW', 'TRIANGLE', 'CIRCLE', 'SQUARE']):
                return False  # Keep these
        except:
            pass
        return True

    # Fullwidth/Halfwidth
    if 0xFF00 <= codepoint <= 0xFFEF:
        return True

    # CJK
    if 0x4E00 <= codepoint <= 0x9FFF:
        return True

    return False


def infer_direction_from_name(name: str) -> str:
    """Infer direction from Unicode character name."""
    name_upper = name.upper()

    if "NORTH" in name_upper or "UPWARD" in name_upper or "UP " in name_upper:
        if "EAST" in name_upper or "RIGHT" in name_upper:
            return "NE"
        elif "WEST" in name_upper or "LEFT" in name_upper:
            return "NW"
        else:
            return "N"

    if "SOUTH" in name_upper or "DOWNWARD" in name_upper or "DOWN " in name_upper:
        if "EAST" in name_upper or "RIGHT" in name_upper:
            return "SE"
        elif "WEST" in name_upper or "LEFT" in name_upper:
            return "SW"
        else:
            return "S"

    if "EAST" in name_upper or "RIGHTWARD" in name_upper or "RIGHT" in name_upper:
        return "E"

    if "WEST" in name_upper or "LEFTWARD" in name_upper or "LEFT" in name_upper:
        return "W"

    if "HORIZONTAL" in name_upper:
        return "EW"

    if "VERTICAL" in name_upper:
        return "NS"

    return ""


def infer_intensity_from_name(name: str) -> float:
    """Infer intensity/weight from Unicode character name."""
    name_upper = name.upper()

    if "HEAVY" in name_upper or "BOLD" in name_upper or "BLACK" in name_upper or "THICK" in name_upper:
        return 0.9

    if "LIGHT" in name_upper or "THIN" in name_upper:
        return 0.3

    if "DOUBLE" in name_upper:
        return 0.85

    return 0.5


def infer_styles_from_name(name: str) -> set:
    """Infer style tags from Unicode character name."""
    name_upper = name.upper()
    styles = set()

    if "ARROW" in name_upper:
        styles.add("arrow")
    if "TRIANGLE" in name_upper:
        styles.add("triangle")
    if "BLOCK" in name_upper or "QUADRANT" in name_upper:
        styles.add("block")
    if "BOX" in name_upper or "LINE" in name_upper:
        styles.add("line")
        styles.add("connector")
    if "CIRCLE" in name_upper or "CIRCLED" in name_upper:
        styles.add("circle")
    if "SQUARE" in name_upper:
        styles.add("square")
    if "DIAMOND" in name_upper:
        styles.add("diamond")
    if "CURVED" in name_upper or "ARC" in name_upper or "ROUNDED" in name_upper:
        styles.add("curved")
        styles.add("organic")
    if "DOUBLE" in name_upper:
        styles.add("double")
    if "DASHED" in name_upper or "DOTTED" in name_upper:
        styles.add("dashed")
    if any(x in name_upper for x in ["GEOMETRIC", "MATHEMATICAL"]):
        styles.add("geometric")

    return styles


def categorize_character(char: str, codepoint_int: int) -> GlyphInfo:
    """Automatically categorize a character."""
    codepoint = f"U+{codepoint_int:04X}"

    try:
        name = unicodedata.name(char)
    except ValueError:
        name = f"UNNAMED_{codepoint}"

    direction_str = infer_direction_from_name(name)
    direction = string_to_direction(direction_str) if direction_str else Direction.NONE
    intensity = infer_intensity_from_name(name)
    styles = infer_styles_from_name(name)

    if intensity < 0.4:
        weight = "light"
    elif intensity > 0.7:
        weight = "heavy"
    else:
        weight = "medium"

    return GlyphInfo(
        char=char,
        codepoint=codepoint,
        directions=direction,
        intensity=intensity,
        styles=styles,
        weight=weight
    )


def scan_range(start: int, end: int, verbose: bool = False):
    """Scan a Unicode range, filtering for single-width characters."""
    glyphs = []
    skipped = 0
    skipped_wide = 0

    for cp in range(start, end + 1):
        if 0xD800 <= cp <= 0xDFFF:  # Skip surrogates
            continue

        try:
            char = chr(cp)
            cat = unicodedata.category(char)

            # Skip control, format, surrogate
            if cat[0] == 'C' or cat in ('Cf', 'Cs'):
                skipped += 1
                continue

            # Skip spaces
            if cat[0] == 'Z':
                skipped += 1
                continue

            # Skip replacement character
            if char == '\uFFFD':
                skipped += 1
                continue

            # CRITICAL: Check if single-width
            if not is_single_width(char):
                skipped_wide += 1
                continue

            # CRITICAL: Filter emoji and wide characters
            if is_emoji_or_wide(char, cp):
                skipped_wide += 1
                continue

            # Categorize
            glyph = categorize_character(char, cp)

            # Only keep if it has useful properties
            if glyph.directions != Direction.NONE or glyph.styles:
                glyphs.append(glyph)
            else:
                skipped += 1

        except (ValueError, UnicodeDecodeError):
            skipped += 1
            continue

    if verbose:
        print(f"  Found {len(glyphs)} single-width glyphs, skipped {skipped} non-useful, {skipped_wide} wide/emoji")

    return glyphs


def add_special_directional(picker: GlyphPicker):
    """Add hand-curated special directional characters (already filtered for single-width)."""
    count = 0
    for char, (codepoint, direction_str, intensity, styles) in SPECIAL_DIRECTIONAL.items():
        # Double-check it's single-width
        if not is_single_width(char):
            continue

        direction = string_to_direction(direction_str) if direction_str else Direction.NONE
        weight = "heavy" if intensity > 0.7 else "light" if intensity < 0.4 else "medium"

        glyph = GlyphInfo(
            char=char,
            codepoint=codepoint,
            directions=direction,
            intensity=intensity,
            styles=set(styles),
            weight=weight
        )
        picker.add_glyph(glyph)
        count += 1

    return count


def main():
    parser = argparse.ArgumentParser(
        description="Build OPTIMIZED glyph database (mobile-friendly, single-width only)"
    )
    parser.add_argument("-o", "--output", default="glyph_database_optimized.json",
                       help="Output JSON file")
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Verbose output")
    args = parser.parse_args()

    picker = GlyphPicker()

    # Add hand-curated directional characters
    print("Adding hand-curated directional characters...")
    count = add_special_directional(picker)
    print(f"  Added {count} special glyphs")

    # Scan optimized ranges (skip problematic ones)
    ranges_to_scan = [
        ("arrows_basic", RANGES["arrows_basic"]),
        ("box_drawing", RANGES["box_drawing"]),
        ("block_elements", RANGES["block_elements"]),
        ("geometric_shapes", RANGES["geometric_shapes"]),
        ("supplemental_arrows_a", RANGES["supplemental_arrows_a"]),
        ("supplemental_arrows_b", RANGES["supplemental_arrows_b"]),
        ("misc_symbols_arrows", RANGES["misc_symbols_arrows"]),
        # Skip: braille (256 glyphs, mostly not directional)
        # Skip: halfwidth_fullwidth (all wide!)
        # Skip: misc_symbols (mostly emoji)
        # Skip: dingbats (some are wide)
    ]

    print(f"\nScanning {len(ranges_to_scan)} optimized Unicode ranges...")
    total_added = 0

    for name, info in ranges_to_scan:
        print(f"\n  {info['name']} (U+{info['start']:04X}..U+{info['end']:04X})")
        glyphs = scan_range(info['start'], info['end'], verbose=args.verbose)

        for glyph in glyphs:
            picker.add_glyph(glyph)

        print(f"    Added {len(glyphs)} glyphs")
        total_added += len(glyphs)

    print(f"\n{'='*60}")
    print(f"Total glyphs in optimized database: {len(picker)}")
    print(f"  (All single-width, no emoji, no fullwidth)")
    print(f"{'='*60}\n")

    # Save
    picker.save_json(args.output)
    print(f"Saved to {args.output}")

    # Show stats
    print("\nDatabase Statistics:")
    print(f"  Directional glyphs: {sum(1 for g in picker.glyphs if g.directions != Direction.NONE)}")
    print(f"  Light weight: {sum(1 for g in picker.glyphs if g.weight == 'light')}")
    print(f"  Medium weight: {sum(1 for g in picker.glyphs if g.weight == 'medium')}")
    print(f"  Heavy weight: {sum(1 for g in picker.glyphs if g.weight == 'heavy')}")

    all_styles = set()
    for g in picker.glyphs:
        all_styles.update(g.styles)
    print(f"  Unique styles: {len(all_styles)}")
    print(f"    {', '.join(sorted(all_styles))}")


if __name__ == "__main__":
    main()
