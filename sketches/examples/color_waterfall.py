#!/usr/bin/env python3
"""
Color Waterfall - High mutation creates rainbow cascades

Example: Crank up mutation and watch colors flow.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.sketchbook import quick_sketch

sketch = quick_sketch(
    walkers=300,
    colors='single',            # Start with one color
    base_hue=0.6,              # Blue
    behavior='levy',            # Lévy flights for varied motion
    mutation_rate=0.15,         # HIGH mutation = color explosion
    spawn_rate=0.2,             # Fast reproduction
    breeding_threshold=0.5,     # Anyone can breed
    fields=['diffusion'],       # Scent trails create glow
    events=True,
    event_pool='aesthetic',
    delay=0.025
)

if __name__ == '__main__':
    print("Color Waterfall: High mutation creates flowing rainbow")
    print("Watch a single color explode into full spectrum")
    print("Press Ctrl-C to exit\n")
    sketch.run()
