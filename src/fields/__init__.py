"""
fields - Grid-based systems for spatial dynamics

Provides abstract Field interface and concrete implementations:
- DiffusionField: Scent trails with spreading and decay
- TerritoryField: Chunked ownership tracking with emergent colors
"""

from .base import Field, ScalarField, DiscreteField
from .diffusion import DiffusionField
from .territory import TerritoryField

__all__ = [
    'Field',
    'ScalarField',
    'DiscreteField',
    'DiffusionField',
    'TerritoryField',
]
