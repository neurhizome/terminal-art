#!/usr/bin/env python3
"""
Direction constants and utilities for directional glyph mapping.

Directions can be combined with bitwise OR to represent diagonal or multi-directional glyphs.
"""
from enum import IntFlag
from typing import Set, Tuple


class Direction(IntFlag):
    """Directional flags for glyph classification.

    Can be combined with | operator for diagonals:
        Direction.N | Direction.E  # Northeast
    """
    NONE = 0
    N = 1      # North (up)
    E = 2      # East (right)
    S = 4      # South (down)
    W = 8      # West (left)

    # Common diagonals (convenience)
    NE = N | E  # 3
    SE = S | E  # 6
    SW = S | W  # 12
    NW = N | W  # 9

    # Bidirectional (straight lines)
    NS = N | S  # 5
    EW = E | W  # 10

    # Multi-directional
    ALL = N | E | S | W  # 15


# Opposite directions for connector logic
OPPOSITES = {
    Direction.N: Direction.S,
    Direction.S: Direction.N,
    Direction.E: Direction.W,
    Direction.W: Direction.E,
}


def get_primary_direction(directions: Direction) -> Direction:
    """Extract the primary (first set) direction from a combined direction."""
    if Direction.N in directions:
        return Direction.N
    if Direction.E in directions:
        return Direction.E
    if Direction.S in directions:
        return Direction.S
    if Direction.W in directions:
        return Direction.W
    return Direction.NONE


def direction_to_vector(direction: Direction) -> Tuple[int, int]:
    """Convert a direction to a (dx, dy) vector.

    For combined directions, returns the average vector.
    """
    dx, dy = 0, 0

    if Direction.N in direction:
        dy -= 1
    if Direction.S in direction:
        dy += 1
    if Direction.E in direction:
        dx += 1
    if Direction.W in direction:
        dx -= 1

    return (dx, dy)


def direction_from_vector(dx: int, dy: int) -> Direction:
    """Convert a (dx, dy) vector to a Direction.

    Examples:
        (1, 0) -> Direction.E
        (1, -1) -> Direction.NE
        (0, 1) -> Direction.S
    """
    result = Direction.NONE

    if dy < 0:
        result |= Direction.N
    elif dy > 0:
        result |= Direction.S

    if dx > 0:
        result |= Direction.E
    elif dx < 0:
        result |= Direction.W

    return result


def direction_to_string(direction: Direction) -> str:
    """Convert Direction to human-readable string.

    Examples:
        Direction.E -> "E"
        Direction.NE -> "NE"
        Direction.N | Direction.S -> "NS"
    """
    if direction == Direction.NONE:
        return "NONE"
    if direction == Direction.ALL:
        return "ALL"

    parts = []
    if Direction.N in direction:
        parts.append("N")
    if Direction.E in direction:
        parts.append("E")
    if Direction.S in direction:
        parts.append("S")
    if Direction.W in direction:
        parts.append("W")

    return "".join(parts)


def string_to_direction(s: str) -> Direction:
    """Convert string like 'NE' or 'E' to Direction.

    Examples:
        'E' -> Direction.E
        'NE' -> Direction.NE
        'NESW' -> Direction.ALL
    """
    s = s.upper().strip()
    result = Direction.NONE

    if 'N' in s:
        result |= Direction.N
    if 'E' in s:
        result |= Direction.E
    if 'S' in s:
        result |= Direction.S
    if 'W' in s:
        result |= Direction.W

    return result
