#!/usr/bin/env python3
"""
ASCIICOLOGY GLYPH SETS
Curated Unicode character collections for generative terminal art

Each set is ordered by visual density/complexity for contrast-based selection
"""

# ============================================================================
# I CHING HEXAGRAMS (U+4DC0 - U+4DFF)
# 64 hexagrams representing all combinations of broken/solid lines
# Perfect for binary-state visualization with ancient symbolic weight
# ============================================================================

HEXAGRAMS_RAW = '䷀䷁䷂䷃䷄䷅䷆䷇䷈䷉䷊䷋䷌䷍䷎䷏䷐䷑䷒䷓䷔䷕䷖䷗䷘䷙䷚䷛䷜䷝䷞䷟䷠䷡䷢䷣䷤䷥䷦䷧䷨䷩䷪䷫䷬䷭䷮䷯䷰䷱䷲䷳䷴䷵䷶䷷䷸䷹䷺䷻䷼䷽䷾䷿'

# Organize by visual density (number of solid lines)
# Lower density = more broken lines, Higher density = more solid lines
HEXAGRAMS_BY_DENSITY = [
    # Sparse (0-2 solid lines)
    '䷁',  # The Receptive (all broken)
    '䷗䷏䷆䷖',  # Mostly broken

    # Light (2-3 solid lines)
    '䷃䷓䷂䷋䷒䷎䷚',

    # Medium-Light (3 solid lines)
    '䷍䷇䷈䷉䷕䷑䷐䷞䷟䷙䷝䷜䷛䷔䷊',

    # Medium (3-4 solid lines balanced)
    '䷌䷄䷅䷘䷡䷠䷟䷞䷢䷣䷤䷥',

    # Medium-Dense (4-5 solid lines)
    '䷦䷧䷨䷩䷪䷫䷬䷭䷮䷯䷰䷱䷲',

    # Dense (5-6 solid lines)
    '䷳䷴䷵䷶䷷䷸䷹䷺䷻䷼䷽䷾',

    # Solid (all solid lines)
    '䷿',  # The Creative
]

HEXAGRAMS = ''.join(HEXAGRAMS_BY_DENSITY)

# Classic I Ching sequence (King Wen order)
HEXAGRAMS_KINGWEN = '䷀䷁䷂䷃䷄䷅䷆䷇䷈䷉䷊䷋䷌䷍䷎䷏䷐䷑䷒䷓䷔䷕䷖䷗䷘䷙䷚䷛䷜䷝䷞䷟䷠䷡䷢䷣䷤䷥䷦䷧䷨䷩䷪䷫䷬䷭䷮䷯䷰䷱䷲䷳䷴䷵䷶䷷䷸䷹䷺䷻䷼䷽䷾䷿'


# ============================================================================
# TAI XUAN JING TETRAGRAMS (U+1D300 - U+1D356)
# 81 tetragrams from ancient Chinese text "Canon of Supreme Mystery"
# Four-line symbols, more granular than hexagrams
# ============================================================================

TETRAGRAMS_RAW = '𝌀𝌁𝌂𝌃𝌄𝌅𝌆𝌇𝌈𝌉𝌊𝌋𝌌𝌍𝌎𝌏𝌐𝌑𝌒𝌓𝌔𝌕𝌖𝌗𝌘𝌙𝌚𝌛𝌜𝌝𝌞𝌟𝌠𝌡𝌢𝌣𝌤𝌥𝌦𝌧𝌨𝌩𝌪𝌫𝌬𝌭𝌮𝌯𝌰𝌱𝌲𝌳𝌴𝌵𝌶𝌷𝌸𝌹𝌺𝌻𝌼𝌽𝌾𝌿𝍀𝍁𝍂𝍃𝍄𝍅𝍆𝍇𝍈𝍉𝍊𝍋𝍌𝍍𝍎𝍏𝍐𝍑𝍒𝍓𝍔𝍕𝍖'

# Organize by visual density (quaternary logic: 0-3 marks per position)
TETRAGRAMS_SPARSE = '𝌀𝌁𝌂𝌃𝌄𝌅𝌆𝌇𝌈𝌉𝌊𝌋𝌌𝌍𝌎𝌏𝌐𝌑𝌒𝌓𝌔'  # Lighter patterns
TETRAGRAMS_MEDIUM = '𝌕𝌖𝌗𝌘𝌙𝌚𝌛𝌜𝌝𝌞𝌟𝌠𝌡𝌢𝌣𝌤𝌥𝌦𝌧𝌨𝌩𝌪𝌫𝌬𝌭𝌮𝌯𝌰𝌱𝌲𝌳𝌴𝌵𝌶𝌷𝌸𝌹𝌺'  # Medium density
TETRAGRAMS_DENSE = '𝌻𝌼𝌽𝌾𝌿𝍀𝍁𝍂𝍃𝍄𝍅𝍆𝍇𝍈𝍉𝍊𝍋𝍌𝍍𝍎𝍏𝍐𝍑𝍒𝍓𝍔𝍕𝍖'  # Denser patterns

TETRAGRAMS = TETRAGRAMS_RAW


# ============================================================================
# BRAILLE PATTERNS (U+2800 - U+28FF)
# 256 unique patterns (2^8 dot positions)
# Perfect for fine-grained density representation
# Each pattern is 2x4 dots, density ranges from 0 (blank) to 8 (all dots)
# ============================================================================

# Generate all 256 Braille patterns
BRAILLE_ALL = ''.join(chr(0x2800 + i) for i in range(256))

# Organize by dot count (visual density)
def count_braille_dots(codepoint):
    """Count number of raised dots in Braille character"""
    offset = codepoint - 0x2800
    return bin(offset).count('1')

# Create density-sorted Braille
_braille_sorted = sorted(range(256), key=lambda i: count_braille_dots(0x2800 + i))
BRAILLE_BY_DENSITY = ''.join(chr(0x2800 + i) for i in _braille_sorted)

# Specific density levels
BRAILLE_EMPTY = '⠀'  # No dots
BRAILLE_SPARSE = ''.join(chr(0x2800 + i) for i in range(256) if count_braille_dots(0x2800 + i) <= 2)
BRAILLE_MEDIUM = ''.join(chr(0x2800 + i) for i in range(256) if 3 <= count_braille_dots(0x2800 + i) <= 5)
BRAILLE_DENSE = ''.join(chr(0x2800 + i) for i in range(256) if count_braille_dots(0x2800 + i) >= 6)
BRAILLE_FULL = '⣿'  # All dots


# ============================================================================
# COMPOSITE GLYPH SETS FOR CONTRAST MAPPING
# ============================================================================

def create_contrast_map(glyph_set, num_levels=None):
    """
    Create a list mapping contrast levels to glyphs

    Args:
        glyph_set: String of glyphs ordered by visual density
        num_levels: Number of contrast levels (default: length of glyph_set)

    Returns:
        List of glyphs for indexing by contrast value
    """
    if num_levels is None:
        return list(glyph_set)

    # Sample evenly across the glyph set
    indices = [int(i * (len(glyph_set) - 1) / (num_levels - 1))
               for i in range(num_levels)]
    return [glyph_set[i] for i in indices]


# POSITIVE SPACE SET: Hexagrams (bold, symbolic)
POSITIVE_HEXAGRAMS = create_contrast_map(HEXAGRAMS, 16)

# NEGATIVE SPACE SET: Braille (subtle, dotted)
NEGATIVE_BRAILLE = create_contrast_map(BRAILLE_BY_DENSITY, 16)

# HYBRID: Tetragrams for medium contrast, Braille for extremes
HYBRID_SET = (
    BRAILLE_SPARSE[:4] +  # Very low contrast
    TETRAGRAMS_SPARSE[:8] +  # Low contrast
    TETRAGRAMS_MEDIUM[:16] +  # Medium contrast
    TETRAGRAMS_DENSE[:8] +  # High contrast
    BRAILLE_DENSE[-4:]  # Very high contrast
)

# DIVINATION SET: Mix hexagrams and tetragrams
DIVINATION_SET = ''.join([
    HEXAGRAMS[i] if i % 2 == 0 else TETRAGRAMS[i % len(TETRAGRAMS)]
    for i in range(32)
])


# ============================================================================
# PRESET POOLS FOR DIFFERENT AESTHETICS
# ============================================================================

POOLS = {
    'hexagrams_sparse': HEXAGRAMS[:32],  # First half (lighter)
    'hexagrams_dense': HEXAGRAMS[32:],   # Second half (denser)
    'hexagrams_all': HEXAGRAMS,

    'tetragrams_sparse': TETRAGRAMS_SPARSE,
    'tetragrams_medium': TETRAGRAMS_MEDIUM,
    'tetragrams_dense': TETRAGRAMS_DENSE,
    'tetragrams_all': TETRAGRAMS,

    'braille_sparse': BRAILLE_SPARSE,
    'braille_medium': BRAILLE_MEDIUM,
    'braille_dense': BRAILLE_DENSE,
    'braille_all': BRAILLE_BY_DENSITY,

    'positive_negative': (HEXAGRAMS, BRAILLE_BY_DENSITY),  # Dual set
    'divination': DIVINATION_SET,
    'hybrid': HYBRID_SET,
}


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

if __name__ == "__main__":
    print("=== ASCIICOLOGY GLYPH SETS ===\n")

    print(f"Hexagrams: {len(HEXAGRAMS)} symbols")
    print(f"Sample: {HEXAGRAMS[:10]}\n")

    print(f"Tetragrams: {len(TETRAGRAMS)} symbols")
    print(f"Sample: {TETRAGRAMS[:10]}\n")

    print(f"Braille patterns: {len(BRAILLE_ALL)} patterns")
    print(f"By density (first 20): {BRAILLE_BY_DENSITY[:20]}\n")

    print("Contrast mapping example (16 levels from hexagrams):")
    print(''.join(POSITIVE_HEXAGRAMS))
    print("\nSame contrast levels using Braille:")
    print(''.join(NEGATIVE_BRAILLE))
