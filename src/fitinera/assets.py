from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

from .cashflows import TaxRate
from .core import Age, GrowthStrategy, NoGrowth, TimeBounds


@dataclass(frozen=True)
class Penalty:
    """Represents a withdrawal penalty."""

    rate: float
    time_bounds: TimeBounds

    def __post_init__(self):
        if not 0.0 <= self.rate <= 1.0:
            raise ValueError("Penalty rate must be between 0.0 and 1.0.")


@dataclass(frozen=True)
class ContributionConstraint:
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
    contribution_priority: int
    withdrawal_priority: int
    growth_strategy: GrowthStrategy = field(default_factory=NoGrowth)
    contribution_constraints: List[ContributionConstraint] = field(default_factory=list)
    withdrawal_penalties: List[Penalty] = field(default_factory=list)
    override_withdrawal_taxes: List[TaxRate] = field(default_factory=list)

    def __post_init__(self):
        if not self.name:
            raise ValueError("Name cannot be empty.")
        if self.initial_value < 0:
            raise ValueError("Initial value cannot be negative.")
        if self.contribution_priority <= 0:
            raise ValueError("Contribution priority must be positive.")
        if self.withdrawal_priority <= 0:
            raise ValueError("Withdrawal priority must be positive.")

    def get_max_contribution(self, current_age: Age) -> float:
        """Get the maximum allowed contribution for the current age."""
        max_contrib = float("inf")
        for constraint in self.contribution_constraints:
            if (
                constraint.effective_time_bounds is None
                or constraint.effective_time_bounds.is_active(current_age)
            ):
                max_contrib = min(max_contrib, constraint.effective_monthly_max)
        return max_contrib

    def get_penalty(self, current_age: Age) -> Optional[Penalty]:
        """Get the withdrawal penalty for the current age, if any."""
        for penalty in self.withdrawal_penalties:
            if penalty.time_bounds.is_active(current_age):
                return penalty
        return None

    def get_override_tax_rate(self, current_age: Age) -> Optional[TaxRate]:
        """Get the override withdrawal tax rate for the current age, if any."""
        for tax_rate in self.override_withdrawal_taxes:
            if tax_rate.time_bounds.is_active(current_age):
                return tax_rate
        return None


class AssetBuilder:
    """A fluent builder for creating Asset instances."""

    def __init__(self, name: str):
        self._name = name
        self._initial_value: float = 0.0
        self._growth_strategy: GrowthStrategy = NoGrowth()
        self._contribution_priority: int = 1
        self._withdrawal_priority: int = 1
        self._contribution_constraints: List[ContributionConstraint] = []
        self._withdrawal_penalties: List[Penalty] = []
        self._override_withdrawal_taxes: List[TaxRate] = []

    def with_initial_value(self, value: float) -> AssetBuilder:
        self._initial_value = value
        return self

    def with_growth_strategy(self, strategy: GrowthStrategy) -> AssetBuilder:
        self._growth_strategy = strategy
        return self

    def with_contribution_priority(self, priority: int) -> AssetBuilder:
        self._contribution_priority = priority
        return self

    def with_withdrawal_priority(self, priority: int) -> AssetBuilder:
        self._withdrawal_priority = priority
        return self

    def with_contribution_constraint(self, constraint: ContributionConstraint) -> AssetBuilder:
        self._contribution_constraints.append(constraint)
        return self

    def with_withdrawal_penalty(self, penalty: Penalty) -> AssetBuilder:
        self._withdrawal_penalties.append(penalty)
        return self

    def with_override_withdrawal_tax(self, tax_rate: TaxRate) -> AssetBuilder:
        self._override_withdrawal_taxes.append(tax_rate)
        return self

    def build(self) -> Asset:
        return Asset(
            name=self._name,
            initial_value=self._initial_value,
            growth_strategy=self._growth_strategy,
            contribution_priority=self._contribution_priority,
            withdrawal_priority=self._withdrawal_priority,
            contribution_constraints=self._contribution_constraints,
            withdrawal_penalties=self._withdrawal_penalties,
            override_withdrawal_taxes=self._override_withdrawal_taxes,
        )
