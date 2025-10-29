from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

from .core import Age, GrowthStrategy, TimeBounds


@dataclass(frozen=True)
class Penalty:
    """Represents a withdrawal penalty."""

    rate: float
    time_bounds: TimeBounds

    def __post_init__(self):
        if not 0.0 <= self.rate <= 1.0:
            raise ValueError("Penalty rate must be between 0.0 and 1.0.")


@dataclass(frozen=True)
class AssetContributionConstraint:
    """Represents a constraint on asset contributions."""

    effective_time_bounds: Optional[TimeBounds] = None
    effective_monthly_max: float = 0.0

    def __post_init__(self):
        if self.effective_monthly_max < 0:
            raise ValueError("Effective monthly max cannot be negative.")


@dataclass(frozen=True)
class Asset:
    """Represents a financial asset."""

    name: str
    initial_value: float
    growth_strategy: GrowthStrategy
    contribution_priority: int
    withdrawal_priority: int
    contribution_constraints: List[AssetContributionConstraint] = field(default_factory=list)
    withdrawal_penalties: List[Penalty] = field(default_factory=list)

    def __post_init__(self):
        if not self.name:
            raise ValueError("Name cannot be empty.")
        if self.initial_value < 0:
            raise ValueError("Initial value cannot be negative.")
        if self.contribution_priority <= 0:
            raise ValueError("Contribution priority must be positive.")
        if self.withdrawal_priority <= 0:
            raise ValueError("Withdrawal priority must be positive.")
