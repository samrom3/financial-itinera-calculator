from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto

from .core import GrowthStrategy, TimeBounds


class IncomeKind(Enum):
    """Enumeration for the different kinds of income."""

    ACTIVE = auto()
    PASSIVE = auto()


@dataclass(frozen=True)
class Income:
    """Represents an income stream."""

    name: str
    monthly_amount: float
    kind: IncomeKind
    growth_strategy: GrowthStrategy
    time_bounds: TimeBounds = TimeBounds()

    def __post_init__(self):
        if not self.name:
            raise ValueError("Name cannot be empty.")


@dataclass(frozen=True)
class Expense:
    """Represents an expense stream."""

    name: str
    monthly_amount: float
    growth_strategy: GrowthStrategy
    time_bounds: TimeBounds = TimeBounds()

    def __post_init__(self):
        if not self.name:
            raise ValueError("Name cannot be empty.")


@dataclass(frozen=True)
class TaxRate:
    """Represents an effective tax rate over a period of time."""

    rate: float
    time_bounds: TimeBounds = TimeBounds()

    def __post_init__(self):
        if not -1.0 < self.rate < 1.0:
            raise ValueError("Tax rate must be between -1.0 and 1.0.")
