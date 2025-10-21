#!/usr/bin/env python3
"""
Comprehensive Unicode range definitions for glyph categorization.

Contains all the interesting ranges for terminal art, with metadata about
what each range contains and suggested default categorization.
"""

# Unicode ranges with directional/visual significance
RANGES = {
    "arrows_basic": {
        "start": 0x2190,
        "end": 0x21FF,
        "name": "Arrows",
        "description": "Basic arrows in all directions",
        "default_styles": ["arrow", "geometric"],
    },
    "box_drawing": {
        "start": 0x2500,
        "end": 0x257F,
        "name": "Box Drawing",
        "description": "Light, heavy, double box-drawing connectors",
        "default_styles": ["line", "connector"],
    },
    "block_elements": {
        "start": 0x2580,
        "end": 0x259F,
        "name": "Block Elements",
        "description": "Partial blocks, shades, density gradients",
        "default_styles": ["block", "fill"],
    },
    "geometric_shapes": {
        "start": 0x25A0,
        "end": 0x25FF,
        "name": "Geometric Shapes",
        "description": "Triangles, circles, diamonds, polygons",
        "default_styles": ["geometric", "shape"],
    },
    "misc_symbols": {
        "start": 0x2600,
        "end": 0x26FF,
        "name": "Miscellaneous Symbols",
        "description": "Including clock faces, arrows, pointing hands",
        "default_styles": ["symbol"],
    },
    "dingbats": {
        "start": 0x2700,
        "end": 0x27BF,
        "name": "Dingbats",
        "description": "Arrows, stars, crosses, decorative elements",
        "default_styles": ["decorative"],
    },
    "braille": {
        "start": 0x2800,
        "end": 0x28FF,
        "name": "Braille Patterns",
        "description": "256 braille dot patterns (subtle directional hints)",
        "default_styles": ["braille", "dots", "subtle"],
    },
    "supplemental_arrows_a": {
        "start": 0x27F0,
        "end": 0x27FF,
        "name": "Supplemental Arrows-A",
        "description": "Additional arrow styles",
        "default_styles": ["arrow"],
    },
    "supplemental_arrows_b": {
        "start": 0x2900,
        "end": 0x297F,
        "name": "Supplemental Arrows-B",
        "description": "More arrow variations",
        "default_styles": ["arrow"],
    },
    "misc_symbols_arrows": {
        "start": 0x2B00,
        "end": 0x2BFF,
        "name": "Miscellaneous Symbols and Arrows",
        "description": "Modern arrow styles and symbols",
        "default_styles": ["arrow", "modern"],
    },
    "halfwidth_fullwidth": {
        "start": 0xFF00,
        "end": 0xFFEF,
        "name": "Halfwidth and Fullwidth Forms",
        "description": "Wide variants of ASCII and symbols",
        "default_styles": ["wide"],
    },
}

# Clock faces with their directional interpretations
CLOCK_FACES = {
    "🕐": ("U+1F550", 1, "E"),      # 1 o'clock → East
    "🕜": ("U+1F55C", 1.5, "ESE"),  # 1:30
    "🕑": ("U+1F551", 2, "ESE"),    # 2 o'clock
    "🕝": ("U+1F55D", 2.5, "SE"),   # 2:30
    "🕒": ("U+1F552", 3, "SE"),     # 3 o'clock → South-East
    "🕞": ("U+1F55E", 3.5, "SSE"),  # 3:30
    "🕓": ("U+1F553", 4, "SSE"),    # 4 o'clock
    "🕟": ("U+1F55F", 4.5, "S"),    # 4:30
    "🕔": ("U+1F554", 5, "S"),      # 5 o'clock → South
    "🕠": ("U+1F560", 5.5, "SSW"),  # 5:30
    "🕕": ("U+1F555", 6, "SSW"),    # 6 o'clock
    "🕡": ("U+1F561", 6.5, "SW"),   # 6:30
    "🕖": ("U+1F556", 7, "SW"),     # 7 o'clock → South-West
    "🕢": ("U+1F562", 7.5, "SWW"),  # 7:30
    "🕗": ("U+1F557", 8, "SWW"),    # 8 o'clock
    "🕣": ("U+1F563", 8.5, "W"),    # 8:30
    "🕘": ("U+1F558", 9, "W"),      # 9 o'clock → West
    "🕤": ("U+1F564", 9.5, "WNW"),  # 9:30
    "🕙": ("U+1F559", 10, "WNW"),   # 10 o'clock
    "🕥": ("U+1F565", 10.5, "NW"),  # 10:30
    "🕚": ("U+1F55A", 11, "NW"),    # 11 o'clock → North-West
    "🕦": ("U+1F566", 11.5, "NWW"), # 11:30
    "🕛": ("U+1F55B", 12, "N"),     # 12 o'clock → North
    "🕧": ("U+1F567", 12.5, "NNE"), # 12:30
}

# Special directional characters
SPECIAL_DIRECTIONAL = {
    # Triangles pointing directions
    "▲": ("U+25B2", "N", 0.8, ["triangle", "geometric", "solid"]),
    "►": ("U+25BA", "E", 0.8, ["triangle", "geometric", "solid"]),
    "▼": ("U+25BC", "S", 0.8, ["triangle", "geometric", "solid"]),
    "◄": ("U+25C4", "W", 0.8, ["triangle", "geometric", "solid"]),
    "△": ("U+25B3", "N", 0.4, ["triangle", "geometric", "outline"]),
    "▷": ("U+25B7", "E", 0.4, ["triangle", "geometric", "outline"]),
    "▽": ("U+25BD", "S", 0.4, ["triangle", "geometric", "outline"]),
    "◁": ("U+25C1", "W", 0.4, ["triangle", "geometric", "outline"]),

    # Chevrons
    "˄": ("U+02C4", "N", 0.3, ["chevron", "light"]),
    "˃": ("U+02C3", "E", 0.3, ["chevron", "light"]),
    "˅": ("U+02C5", "S", 0.3, ["chevron", "light"]),
    "˂": ("U+02C2", "W", 0.3, ["chevron", "light"]),

    # Half blocks (directional fills)
    "▀": ("U+2580", "N", 0.5, ["block", "half", "fill"]),
    "▄": ("U+2584", "S", 0.5, ["block", "half", "fill"]),
    "▌": ("U+258C", "W", 0.5, ["block", "half", "fill"]),
    "▐": ("U+2590", "E", 0.5, ["block", "half", "fill"]),

    # Quarter blocks
    "▘": ("U+2598", "NW", 0.25, ["block", "quarter", "fill"]),
    "▝": ("U+259D", "NE", 0.25, ["block", "quarter", "fill"]),
    "▖": ("U+2596", "SW", 0.25, ["block", "quarter", "fill"]),
    "▗": ("U+2597", "SE", 0.25, ["block", "quarter", "fill"]),

    # Density gradients (subtle intensity)
    "░": ("U+2591", "", 0.25, ["shade", "light", "fill"]),
    "▒": ("U+2592", "", 0.5, ["shade", "medium", "fill"]),
    "▓": ("U+2593", "", 0.75, ["shade", "heavy", "fill"]),
    "█": ("U+2588", "", 1.0, ["block", "solid", "fill"]),
}

def get_all_ranges():
    """Return all defined ranges."""
    return RANGES

def get_range_info(range_name: str):
    """Get info about a specific range."""
    return RANGES.get(range_name)

def list_ranges():
    """Print all available ranges with descriptions."""
    print("Available Unicode Ranges:\n")
    for key, info in RANGES.items():
        print(f"  {key:25s} U+{info['start']:04X}..U+{info['end']:04X}  {info['name']}")
        print(f"  {'':27s} {info['description']}")
        print()
