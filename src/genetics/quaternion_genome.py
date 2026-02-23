#!/usr/bin/env python3
"""
quaternion_genome.py - Non-commutative color genetics via unit quaternions

A genome where colour is encoded as a point on S³ (the unit 3-sphere) using
a quaternion q = (qw, qi, qj, qk):

    qw  →  brightness  (scalar / 'real' part)
    qi  →  hue (cosine component of the equatorial angle)
    qj  →  hue (sine component of the equatorial angle)
    qk  →  resonance affinity  (the 'k' axis — a coupling strength hidden from
            direct perception but governing how powerfully this walker pulls its
            offspring toward coherence with its partner)

Reproduction is via the Hamilton quaternion product followed by normalisation.
Because quaternion multiplication is non-commutative:

    parent_A.reproduce_with(parent_B) ≠ parent_B.reproduce_with(parent_A)

Parent order matters.  A walker who initiates the encounter is the 'dominant'
parent; its child lands closer to (self_q × other_q) than to self_q alone.

This is the analogue of BLUECOW009's quaternionic oscillator coupling:
the qk component is the coupling strength that determines whether a pair of
walkers pulls toward coherence or slides past each other.  The 'golden middle'
— the coupling strength where the population self-organises rather than
collapsing or drifting — is tunable via the initial affinity parameter.

Drop-in compatible with Genome: exposes the same public interface
(color_h, vigor, saturation, value, to_rgb, reproduce_with, can_breed_with,
distance_to) so Walker and Spawner work without modification.
"""

import math
import random
from typing import Dict, Any, Tuple
from dataclasses import dataclass, field


# ── quaternion arithmetic (Hamilton product) ──────────────────────────────────

def _qmul(q1: Tuple, q2: Tuple) -> Tuple:
    """Hamilton product of two quaternions (w, i, j, k)."""
    w1, i1, j1, k1 = q1
    w2, i2, j2, k2 = q2
    return (
        w1*w2 - i1*i2 - j1*j2 - k1*k2,
        w1*i2 + i1*w2 + j1*k2 - k1*j2,
        w1*j2 - i1*k2 + j1*w2 + k1*i2,
        w1*k2 + i1*j2 - j1*i2 + k1*w2,
    )


def _qnorm(q: Tuple) -> float:
    return math.sqrt(sum(x * x for x in q))


def _qnormalize(q: Tuple) -> Tuple:
    n = _qnorm(q)
    if n < 1e-9:
        return (1.0, 0.0, 0.0, 0.0)
    return tuple(x / n for x in q)


def _qslerp(q1: Tuple, q2: Tuple, t: float) -> Tuple:
    """Spherical linear interpolation between two unit quaternions."""
    dot = sum(a * b for a, b in zip(q1, q2))
    # Use shortest arc
    if dot < 0.0:
        q2 = tuple(-x for x in q2)
        dot = -dot
    dot = min(1.0, dot)
    if dot > 0.9995:
        # Nearly parallel: linear interpolation
        r = tuple(a + t * (b - a) for a, b in zip(q1, q2))
        return _qnormalize(r)
    theta = math.acos(dot)
    sin_theta = math.sin(theta)
    f1 = math.sin((1.0 - t) * theta) / sin_theta
    f2 = math.sin(t * theta) / sin_theta
    return tuple(f1 * a + f2 * b for a, b in zip(q1, q2))


# ── QuaternionGenome ──────────────────────────────────────────────────────────

@dataclass
class QuaternionGenome:
    """
    Quaternion-encoded colour genome with non-commutative inheritance.

    The unit quaternion q = (qw, qi, qj, qk) lives on S³.

    Visual mapping (for rendering):
        hue         = atan2(qj, qi) / 2π          ∈ [0, 1)
        saturation  = sqrt(qi² + qj²)             ∈ [0, 1]
        value       = 0.5 + 0.5 * qw              ∈ [0, 1]
        affinity    = |qk|                         ∈ [0, 1]

    The 'affinity' (|qk|) component is the coupling strength.  It is
    invisible in the HSV colour but governs how powerfully reproduction
    pulls offspring toward coherence.  High-affinity walkers glow — their
    children converge faster and travel farther from the parent's colour.
    """

    qw: float = 0.0    # scalar   → brightness
    qi: float = 1.0    # imag. i  → hue cos
    qj: float = 0.0    # imag. j  → hue sin
    qk: float = 0.0    # imag. k  → resonance affinity (coupling strength)
    vigor: float = 1.0
    traits: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self._normalize()
        self.vigor = max(0.0, self.vigor)

    # ── constructors ──────────────────────────────────────────────────────────

    @classmethod
    def from_hue(cls, hue: float, affinity: float = 0.25,
                 brightness: float = 0.8, vigor: float = 1.0) -> 'QuaternionGenome':
        """
        Create from HSV-like parameters.

        Args:
            hue:        Hue in [0, 1)  — encodes as i-j equatorial rotation
            affinity:   Coupling strength in [0, 1)  — the k component
            brightness: Value-like parameter [0, 1]  — encodes as qw
            vigor:      Fitness weight
        """
        angle = hue * 2.0 * math.pi
        # Equatorial components carry the hue angle
        ij_mag = math.sqrt(1.0 - affinity ** 2) if affinity < 1.0 else 0.0
        qi = ij_mag * math.cos(angle)
        qj = ij_mag * math.sin(angle)
        qk = affinity
        # qw carries brightness, orthogonal to the hue components
        qw = (brightness - 0.5) * 0.5   # small scalar tilt
        g = cls(qw=qw, qi=qi, qj=qj, qk=qk, vigor=vigor)
        g._normalize()
        return g

    # ── genome interface (Walker / Spawner compatible) ────────────────────────

    @property
    def color_h(self) -> float:
        """Hue extracted from the i-j equatorial angle."""
        h = math.atan2(self.qj, self.qi) / (2.0 * math.pi)
        return h % 1.0

    @color_h.setter
    def color_h(self, value: float):
        """Set hue by rotating the i-j components (preserves qk and qw)."""
        angle = value * 2.0 * math.pi
        ij_mag = math.sqrt(self.qi ** 2 + self.qj ** 2)
        if ij_mag < 1e-9:
            ij_mag = math.sqrt(1.0 - self.qk ** 2 - self.qw ** 2)
            ij_mag = max(0.0, ij_mag)
        self.qi = ij_mag * math.cos(angle)
        self.qj = ij_mag * math.sin(angle)
        self._normalize()

    @property
    def saturation(self) -> float:
        """Colour saturation from equatorial (i-j) magnitude."""
        return min(1.0, math.sqrt(self.qi ** 2 + self.qj ** 2))

    @property
    def value(self) -> float:
        """Brightness from scalar qw component."""
        return max(0.0, min(1.0, 0.5 + 0.5 * self.qw))

    @property
    def resonance_affinity(self) -> float:
        """Coupling strength |qk| ∈ [0, 1]."""
        return abs(self.qk)

    # ── reproduction (non-commutative) ────────────────────────────────────────

    def reproduce_with(self, other: 'QuaternionGenome',
                       mutation_rate: float = 0.03) -> 'QuaternionGenome':
        """
        Non-commutative quaternion reproduction.

        Child quaternion is interpolated between self and the Hamilton product
        (self_q × other_q), blended by the caller's resonance affinity.

            self.reproduce_with(other)  ≠  other.reproduce_with(self)

        The dominant parent (self) shapes the child's hue more strongly.
        High affinity (|qk|) in either parent increases coupling — the child
        lands farther from the dominant parent toward the product.

        Args:
            other:         Partner genome
            mutation_rate: Gaussian noise added to each component post-blend
        """
        q_self  = (self.qw,  self.qi,  self.qj,  self.qk)
        q_other = (other.qw, other.qi, other.qj, other.qk)

        # Hamilton product: self × other  (non-commutative)
        q_prod = _qmul(q_self, q_other)
        q_prod = _qnormalize(q_prod)

        # Coupling strength = geometric mean of both parents' affinity.
        # This is the BLUECOW009 "coupling parameter" — governs how far
        # the child moves toward the product (vs staying near dominant parent).
        coupling = math.sqrt(self.resonance_affinity * other.resonance_affinity)
        coupling = max(0.05, min(0.95, coupling))

        # SLERP from self to product, interpolated by coupling strength
        q_child = _qslerp(q_self, q_prod, coupling)

        # Mutation: small Gaussian noise on each component
        q_child = tuple(
            c + random.gauss(0, mutation_rate * 0.3)
            for c in q_child
        )
        q_child = _qnormalize(q_child)

        # Vigor: average with small variation
        child_vigor = ((self.vigor + other.vigor) / 2) * random.uniform(0.9, 1.1)

        return QuaternionGenome(
            qw=q_child[0],
            qi=q_child[1],
            qj=q_child[2],
            qk=q_child[3],
            vigor=child_vigor,
        )

    # ── compatibility ─────────────────────────────────────────────────────────

    def distance_to(self, other: 'QuaternionGenome') -> float:
        """
        Angular distance between two unit quaternions, normalised to [0, 1].

        Uses the quaternion dot-product: identical quaternions → 0,
        maximally different (antipodal on S³) → 1.
        """
        dot = abs(
            self.qw * other.qw +
            self.qi * other.qi +
            self.qj * other.qj +
            self.qk * other.qk
        )
        dot = min(1.0, dot)
        # acos(dot) ∈ [0, π/2] for unit quaternions (we use |dot|)
        return math.acos(dot) / (math.pi / 2)

    def can_breed_with(self, other: 'QuaternionGenome',
                       threshold: float = 0.4) -> bool:
        """Reproductive compatibility by quaternion distance."""
        return self.distance_to(other) < threshold

    def mutate(self, rate: float = 0.05) -> 'QuaternionGenome':
        """Return a mutated copy."""
        q = (
            self.qw + random.gauss(0, rate),
            self.qi + random.gauss(0, rate),
            self.qj + random.gauss(0, rate),
            self.qk + random.gauss(0, rate),
        )
        q = _qnormalize(q)
        return QuaternionGenome(
            qw=q[0], qi=q[1], qj=q[2], qk=q[3],
            vigor=max(0.1, self.vigor * random.uniform(0.85, 1.15)),
        )

    # ── display ───────────────────────────────────────────────────────────────

    def to_rgb(self) -> Tuple[int, int, int]:
        """Convert to RGB for terminal rendering."""
        import colorsys
        # Boost saturation slightly so colours read clearly on dark background
        sat = min(1.0, self.saturation + 0.2)
        r, g, b = colorsys.hsv_to_rgb(self.color_h, sat, self.value)
        return int(r * 255), int(g * 255), int(b * 255)

    # ── internal ──────────────────────────────────────────────────────────────

    def _normalize(self):
        q = (self.qw, self.qi, self.qj, self.qk)
        q = _qnormalize(q)
        self.qw, self.qi, self.qj, self.qk = q

    def __repr__(self) -> str:
        return (
            f"QGenome(h={self.color_h:.3f}, "
            f"aff={self.resonance_affinity:.3f}, "
            f"v={self.value:.3f})"
        )
