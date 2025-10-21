#!/usr/bin/env python3
"""
Build a comprehensive directional glyph database by scanning multiple Unicode ranges.

This tool provides semi-automated categorization based on Unicode properties,
character names, and visual patterns.
"""
import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.glyphs import GlyphInfo, Direction, GlyphPicker
from src.glyphs.direction import string_to_direction
from tools.unicode_ranges import RANGES, SPECIAL_DIRECTIONAL, CLOCK_FACES

try:
    from wcwidth import wcwidth
except ImportError:
    def wcwidth(c):
        cat = unicodedata.category(c)
        return 0 if cat[0] in ('C', 'Z') or unicodedata.combining(c) else 1


def infer_direction_from_name(name: str) -> str:
    """Infer direction from Unicode character name."""
    name_upper = name.upper()

    # Explicit directions in name
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

    # Bidirectional
    if "HORIZONTAL" in name_upper or ("LEFT" in name_upper and "RIGHT" in name_upper):
        return "EW"

    if "VERTICAL" in name_upper or ("UP" in name_upper and "DOWN" in name_upper):
        return "NS"

    return ""


def infer_intensity_from_name(name: str) -> float:
    """Infer intensity/weight from Unicode character name."""
    name_upper = name.upper()

    # Heavy/bold variants
    if "HEAVY" in name_upper or "BOLD" in name_upper or "BLACK" in name_upper or "THICK" in name_upper:
        return 0.9

    # Light variants
    if "LIGHT" in name_upper or "THIN" in name_upper:
        return 0.3

    # Double lines
    if "DOUBLE" in name_upper:
        return 0.85

    # Medium/default
    return 0.5


def infer_styles_from_name(name: str) -> set:
    """Infer style tags from Unicode character name."""
    name_upper = name.upper()
    styles = set()

    # Shape types
    if "ARROW" in name_upper:
        styles.add("arrow")
    if "TRIANGLE" in name_upper:
        styles.add("triangle")
    if "BLOCK" in name_upper or "QUADRANT" in name_upper:
        styles.add("block")
    if "BOX" in name_upper or "LINE" in name_upper:
        styles.add("line")
    if "CIRCLE" in name_upper or "CIRCLED" in name_upper:
        styles.add("circle")
    if "SQUARE" in name_upper:
        styles.add("square")
    if "DIAMOND" in name_upper:
        styles.add("diamond")

    # Style modifiers
    if "CURVED" in name_upper or "ARC" in name_upper or "ROUNDED" in name_upper:
        styles.add("curved")
        styles.add("organic")
    if "DOUBLE" in name_upper:
        styles.add("double")
    if "DASHED" in name_upper or "DOTTED" in name_upper:
        styles.add("dashed")
    if "WIDE" in name_upper or "LONG" in name_upper:
        styles.add("long")

    # Geometric vs organic
    if any(x in name_upper for x in ["GEOMETRIC", "MATHEMATICAL"]):
        styles.add("geometric")

    return styles


def categorize_character(char: str, codepoint_int: int, range_info: dict = None) -> GlyphInfo:
    """Automatically categorize a character based on Unicode metadata."""
    codepoint = f"U+{codepoint_int:04X}"

    try:
        name = unicodedata.name(char)
    except ValueError:
        name = f"UNNAMED_{codepoint}"

    # Infer properties from name
    direction_str = infer_direction_from_name(name)
    direction = string_to_direction(direction_str) if direction_str else Direction.NONE
    intensity = infer_intensity_from_name(name)
    styles = infer_styles_from_name(name)

    # Add range default styles if provided
    if range_info and "default_styles" in range_info:
        styles.update(range_info["default_styles"])

    # Determine weight category
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


def scan_range(start: int, end: int, range_info: dict = None, verbose: bool = False):
    """Scan a Unicode range and categorize characters."""
    glyphs = []
    skipped = 0

    for cp in range(start, end + 1):
        # Skip surrogates
        if 0xD800 <= cp <= 0xDFFF:
            continue

        try:
            char = chr(cp)
            cat = unicodedata.category(char)

            # Skip control, format, surrogate characters
            if cat[0] == 'C' or cat in ('Cf', 'Cs'):
                skipped += 1
                continue

            # Skip spaces unless they're interesting
            if cat[0] == 'Z':
                skipped += 1
                continue

            # Skip replacement character
            if char == '\uFFFD':
                skipped += 1
                continue

            # Check if it has positive width
            if wcwidth(char) <= 0:
                skipped += 1
                continue

            # Categorize
            glyph = categorize_character(char, cp, range_info)

            # Only keep if it has some useful property
            if glyph.directions != Direction.NONE or glyph.styles:
                glyphs.append(glyph)
            else:
                skipped += 1

        except (ValueError, UnicodeDecodeError):
            skipped += 1
            continue

    if verbose:
        print(f"  Found {len(glyphs)} glyphs, skipped {skipped}")

    return glyphs


def add_special_directional(picker: GlyphPicker):
    """Add hand-curated special directional characters."""
    count = 0
    for char, (codepoint, direction_str, intensity, styles) in SPECIAL_DIRECTIONAL.items():
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


def add_clock_faces(picker: GlyphPicker):
    """Add clock faces with their directional interpretations."""
    count = 0
    for char, (codepoint, hour, direction_str) in CLOCK_FACES.items():
        direction = string_to_direction(direction_str) if direction_str else Direction.NONE

        # Intensity based on time (arbitrary but consistent)
        intensity = 0.3 + (hour / 12.0) * 0.4  # Range: 0.3 to 0.7

        glyph = GlyphInfo(
            char=char,
            codepoint=codepoint,
            directions=direction,
            intensity=intensity,
            styles={"clock", "symbol", "circular"},
            weight="medium"
        )
        picker.add_glyph(glyph)
        count += 1

    return count


def main():
    parser = argparse.ArgumentParser(
        description="Build comprehensive directional glyph database"
    )
    parser.add_argument("-o", "--output", default="glyph_database_full.json",
                       help="Output JSON file")
    parser.add_argument("--ranges", nargs="+",
                       help="Specific ranges to scan (e.g., arrows_basic box_drawing)")
    parser.add_argument("--all-ranges", action="store_true",
                       help="Scan all defined ranges")
    parser.add_argument("--list-ranges", action="store_true",
                       help="List available ranges and exit")
    parser.add_argument("--merge", help="Merge with existing database")
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Verbose output")
    args = parser.parse_args()

    if args.list_ranges:
        from tools.unicode_ranges import list_ranges
        list_ranges()
        return

    # Start with existing database if merging
    if args.merge:
        print(f"Loading existing database: {args.merge}")
        picker = GlyphPicker.from_json(args.merge)
        print(f"  Loaded {len(picker)} existing glyphs")
    else:
        picker = GlyphPicker()

    # Add hand-curated special characters first
    print("Adding hand-curated directional characters...")
    count = add_special_directional(picker)
    print(f"  Added {count} special directional glyphs")

    print("Adding clock faces...")
    count = add_clock_faces(picker)
    print(f"  Added {count} clock face glyphs")

    # Scan ranges
    if args.all_ranges:
        ranges_to_scan = list(RANGES.keys())
    elif args.ranges:
        ranges_to_scan = args.ranges
    else:
        # Default: scan the most useful ranges
        ranges_to_scan = [
            "arrows_basic",
            "box_drawing",
            "block_elements",
            "geometric_shapes",
            "supplemental_arrows_a",
            "misc_symbols_arrows",
        ]

    print(f"\nScanning {len(ranges_to_scan)} Unicode ranges...")
    total_added = 0

    for range_name in ranges_to_scan:
        if range_name not in RANGES:
            print(f"  Warning: Unknown range '{range_name}', skipping")
            continue

        info = RANGES[range_name]
        print(f"\n  {info['name']} (U+{info['start']:04X}..U+{info['end']:04X})")
        glyphs = scan_range(info['start'], info['end'], info, verbose=args.verbose)

        for glyph in glyphs:
            picker.add_glyph(glyph)

        print(f"    Added {len(glyphs)} glyphs")
        total_added += len(glyphs)

    print(f"\n{'='*60}")
    print(f"Total glyphs in database: {len(picker)}")
    print(f"  (Added {total_added} from range scans)")
    print(f"{'='*60}\n")

    # Save
    picker.save_json(args.output)
    print(f"Saved to {args.output}")

    # Show some stats
    print("\nDatabase Statistics:")
    print(f"  Directional glyphs: {sum(1 for g in picker.glyphs if g.directions != Direction.NONE)}")
    print(f"  Light weight: {sum(1 for g in picker.glyphs if g.weight == 'light')}")
    print(f"  Medium weight: {sum(1 for g in picker.glyphs if g.weight == 'medium')}")
    print(f"  Heavy weight: {sum(1 for g in picker.glyphs if g.weight == 'heavy')}")

    # Count styles
    all_styles = set()
    for g in picker.glyphs:
        all_styles.update(g.styles)
    print(f"  Unique styles: {len(all_styles)}")
    print(f"    {', '.join(sorted(all_styles))}")


if __name__ == "__main__":
    main()
