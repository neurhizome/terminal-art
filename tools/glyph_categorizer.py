#!/usr/bin/env python3
"""
Interactive tool for categorizing Unicode glyphs by direction, intensity, and style.

This helps build the glyph database for the directional picker system.
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


def scan_range(start: int, end: int):
    """Scan a Unicode range and return potentially useful characters."""
    chars = []
    for cp in range(start, end + 1):
        if 0xD800 <= cp <= 0xDFFF:  # Skip surrogates
            continue

        try:
            ch = chr(cp)
            cat = unicodedata.category(ch)

            # Skip control characters, spaces, etc.
            if cat[0] in ('C', 'Z'):
                continue

            # Skip replacement character
            if ch == '\uFFFD':
                continue

            codepoint = f"U+{cp:04X}"
            chars.append((ch, codepoint))

        except (ValueError, UnicodeDecodeError):
            continue

    return chars


def display_grid(chars, cols=16):
    """Display characters in a grid format."""
    for i in range(0, len(chars), cols):
        row = chars[i:i+cols]
        # Display characters
        print("  ", end="")
        for ch, _ in row:
            print(f"{ch} ", end="")
        print()
        # Display codepoints
        print("  ", end="")
        for _, cp in row:
            print(f"{cp[-4:]} ", end="")
        print("\n")


def quick_categorize_arrows():
    """Quick-start: categorize common arrow characters."""
    # Arrow characters
    arrows = [
        ("←", "U+2190", Direction.W, 0.7, {"arrow", "geometric"}),
        ("↑", "U+2191", Direction.N, 0.7, {"arrow", "geometric"}),
        ("→", "U+2192", Direction.E, 0.7, {"arrow", "geometric"}),
        ("↓", "U+2193", Direction.S, 0.7, {"arrow", "geometric"}),
        ("↔", "U+2194", Direction.E | Direction.W, 0.7, {"arrow", "geometric"}),
        ("↕", "U+2195", Direction.N | Direction.S, 0.7, {"arrow", "geometric"}),
        ("↖", "U+2196", Direction.NW, 0.7, {"arrow", "geometric"}),
        ("↗", "U+2197", Direction.NE, 0.7, {"arrow", "geometric"}),
        ("↘", "U+2198", Direction.SE, 0.7, {"arrow", "geometric"}),
        ("↙", "U+2199", Direction.SW, 0.7, {"arrow", "geometric"}),
        ("⇐", "U+21D0", Direction.W, 0.9, {"arrow", "geometric", "double"}),
        ("⇑", "U+21D1", Direction.N, 0.9, {"arrow", "geometric", "double"}),
        ("⇒", "U+21D2", Direction.E, 0.9, {"arrow", "geometric", "double"}),
        ("⇓", "U+21D3", Direction.S, 0.9, {"arrow", "geometric", "double"}),
        ("⟵", "U+27F5", Direction.W, 0.8, {"arrow", "long"}),
        ("⟶", "U+27F6", Direction.E, 0.8, {"arrow", "long"}),
        ("⟷", "U+27F7", Direction.E | Direction.W, 0.8, {"arrow", "long"}),
    ]

    picker = GlyphPicker()
    for char, cp, direction, intensity, styles in arrows:
        glyph = GlyphInfo(
            char=char,
            codepoint=cp,
            directions=direction,
            intensity=intensity,
            styles=styles,
            weight="medium"
        )
        picker.add_glyph(glyph)

    return picker


def quick_categorize_box_drawing():
    """Quick-start: categorize box-drawing connector characters."""
    # Box drawing - light
    box_light = [
        ("─", "U+2500", Direction.E | Direction.W, 0.3, {"line", "connector", "light"}),
        ("│", "U+2502", Direction.N | Direction.S, 0.3, {"line", "connector", "light"}),
        ("┌", "U+250C", Direction.E | Direction.S, 0.3, {"line", "connector", "corner", "light"}),
        ("┐", "U+2510", Direction.W | Direction.S, 0.3, {"line", "connector", "corner", "light"}),
        ("└", "U+2514", Direction.N | Direction.E, 0.3, {"line", "connector", "corner", "light"}),
        ("┘", "U+2518", Direction.N | Direction.W, 0.3, {"line", "connector", "corner", "light"}),
        ("├", "U+251C", Direction.N | Direction.E | Direction.S, 0.3, {"line", "connector", "junction", "light"}),
        ("┤", "U+2524", Direction.N | Direction.W | Direction.S, 0.3, {"line", "connector", "junction", "light"}),
        ("┬", "U+252C", Direction.E | Direction.S | Direction.W, 0.3, {"line", "connector", "junction", "light"}),
        ("┴", "U+2534", Direction.N | Direction.E | Direction.W, 0.3, {"line", "connector", "junction", "light"}),
        ("┼", "U+253C", Direction.ALL, 0.3, {"line", "connector", "junction", "light"}),
    ]

    # Box drawing - heavy
    box_heavy = [
        ("━", "U+2501", Direction.E | Direction.W, 0.8, {"line", "connector", "heavy"}),
        ("┃", "U+2503", Direction.N | Direction.S, 0.8, {"line", "connector", "heavy"}),
        ("┏", "U+250F", Direction.E | Direction.S, 0.8, {"line", "connector", "corner", "heavy"}),
        ("┓", "U+2513", Direction.W | Direction.S, 0.8, {"line", "connector", "corner", "heavy"}),
        ("┗", "U+2517", Direction.N | Direction.E, 0.8, {"line", "connector", "corner", "heavy"}),
        ("┛", "U+251B", Direction.N | Direction.W, 0.8, {"line", "connector", "corner", "heavy"}),
        ("┣", "U+2523", Direction.N | Direction.E | Direction.S, 0.8, {"line", "connector", "junction", "heavy"}),
        ("┫", "U+252B", Direction.N | Direction.W | Direction.S, 0.8, {"line", "connector", "junction", "heavy"}),
        ("┳", "U+2533", Direction.E | Direction.S | Direction.W, 0.8, {"line", "connector", "junction", "heavy"}),
        ("┻", "U+253B", Direction.N | Direction.E | Direction.W, 0.8, {"line", "connector", "junction", "heavy"}),
        ("╋", "U+254B", Direction.ALL, 0.8, {"line", "connector", "junction", "heavy"}),
    ]

    # Rounded corners
    box_rounded = [
        ("╭", "U+256D", Direction.E | Direction.S, 0.3, {"line", "connector", "corner", "rounded", "organic"}),
        ("╮", "U+256E", Direction.W | Direction.S, 0.3, {"line", "connector", "corner", "rounded", "organic"}),
        ("╯", "U+256F", Direction.N | Direction.W, 0.3, {"line", "connector", "corner", "rounded", "organic"}),
        ("╰", "U+2570", Direction.N | Direction.E, 0.3, {"line", "connector", "corner", "rounded", "organic"}),
    ]

    picker = GlyphPicker()
    for char, cp, direction, intensity, styles in box_light + box_heavy + box_rounded:
        weight = "heavy" if "heavy" in styles else "light"
        glyph = GlyphInfo(
            char=char,
            codepoint=cp,
            directions=direction,
            intensity=intensity,
            styles=styles,
            weight=weight
        )
        picker.add_glyph(glyph)

    return picker


def main():
    parser = argparse.ArgumentParser(description="Build directional glyph database")
    parser.add_argument("--output", "-o", default="glyph_database.json", help="Output JSON file")
    parser.add_argument("--quick-start", action="store_true", help="Generate starter database with arrows and box drawing")
    parser.add_argument("--scan", help="Scan Unicode range (format: 0x2500-0x259F)")
    parser.add_argument("--merge", help="Merge with existing JSON file")
    args = parser.parse_args()

    if args.quick_start:
        print("Generating quick-start glyph database...")
        print("  - Adding arrows...")
        picker = quick_categorize_arrows()
        print(f"    Added {len(picker)} arrow glyphs")

        print("  - Adding box-drawing connectors...")
        box_picker = quick_categorize_box_drawing()
        for glyph in box_picker.glyphs:
            picker.add_glyph(glyph)
        print(f"    Added {len(box_picker)} box-drawing glyphs")

        print(f"\nTotal: {len(picker)} glyphs")
        picker.save_json(args.output)
        print(f"Saved to {args.output}")

        # Show some examples
        print("\nExample queries:")
        print(f"  East, light:  {picker.get(direction=Direction.E, intensity=0.3)}")
        print(f"  East, heavy:  {picker.get(direction=Direction.E, intensity=0.8)}")
        print(f"  North, light: {picker.get(direction=Direction.N, intensity=0.3)}")
        print(f"  SE diagonal:  {picker.get(direction=Direction.SE, intensity=0.5)}")

    elif args.scan:
        # Parse range
        if '-' in args.scan:
            start_str, end_str = args.scan.split('-')
            start = int(start_str, 16) if start_str.startswith('0x') else int(start_str)
            end = int(end_str, 16) if end_str.startswith('0x') else int(end_str)
        else:
            print("Range must be in format: 0x2500-0x259F")
            sys.exit(1)

        print(f"Scanning U+{start:04X} to U+{end:04X}...")
        chars = scan_range(start, end)
        print(f"Found {len(chars)} characters:\n")
        display_grid(chars)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
