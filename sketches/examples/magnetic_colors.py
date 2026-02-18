#!/usr/bin/env python3
"""
Magnetic Colors - Walkers attracted to similar hues

Example of quick experimentation with the sketchbook system.
"""

import sys
import os

# Add parent to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.sketchbook import quick_sketch

# Quick setup - just the idea!
sketch = quick_sketch(
    walkers=250,
    colors='rainbow',           # Start with full spectrum
    behavior='random',
    breeding_threshold=0.2,     # Only breed with similar colors
    spawn_rate=0.1,
    mutation_rate=0.04,         # Slow drift through color space
    fields=['territory'],
    events=False,               # Disable events to see pure pattern
    delay=0.03
)

# Run it!
if __name__ == '__main__':
    print("Magnetic Colors: Similar hues attract, opposites repel")
    print("Watch for color clustering and spatial segregation")
    print("Press Ctrl-C to exit\n")
    sketch.run()
