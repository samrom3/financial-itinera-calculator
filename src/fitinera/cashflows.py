from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto

from .core import GrowthStrategy, NoGrowth, TimeBounds


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
    growth_strategy: GrowthStrategy = field(default_factory=NoGrowth)
    time_bounds: TimeBounds = TimeBounds()

    def __post_init__(self):
        if not self.name:
            raise ValueError("Name cannot be empty.")


@dataclass(frozen=True)
class Expense:
    """Represents an expense stream."""

    name: str
    monthly_amount: float
    growth_strategy: GrowthStrategy = field(default_factory=NoGrowth)
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


class IncomeBuilder:
    """A fluent builder for creating Income instances."""

    def __init__(self, name: str, monthly_amount: float):
        self._name = name
        self._monthly_amount = monthly_amount
        self._kind: IncomeKind = IncomeKind.ACTIVE
        self._growth_strategy: GrowthStrategy = NoGrowth()
        self._time_bounds: TimeBounds = TimeBounds()

    def is_active_income(self) -> IncomeBuilder:
        self._kind = IncomeKind.ACTIVE
        return self

    def is_passive_income(self) -> IncomeBuilder:
        self._kind = IncomeKind.PASSIVE
        return self

    def with_growth_strategy(self, strategy: GrowthStrategy) -> IncomeBuilder:
        self._growth_strategy = strategy
        return self

    def with_time_bounds(self, time_bounds: TimeBounds) -> IncomeBuilder:
        self._time_bounds = time_bounds
        return self

    def build(self) -> Income:
        return Income(
            name=self._name,
            monthly_amount=self._monthly_amount,
            kind=self._kind,
            growth_strategy=self._growth_strategy,
            time_bounds=self._time_bounds,
        )


class ExpenseBuilder:
    """A fluent builder for creating Expense instances."""

    def __init__(self, name: str, monthly_amount: float):
        self._name = name
        self._monthly_amount = monthly_amount
        self._growth_strategy: GrowthStrategy = NoGrowth()
        self._time_bounds: TimeBounds = TimeBounds()

    def with_growth_strategy(self, strategy: GrowthStrategy) -> ExpenseBuilder:
        self._growth_strategy = strategy
        return self

    def with_time_bounds(self, time_bounds: TimeBounds) -> ExpenseBuilder:
        self._time_bounds = time_bounds
        return self

    def build(self) -> Expense:
        return Expense(
            name=self._name,
            monthly_amount=self._monthly_amount,
            growth_strategy=self._growth_strategy,
            time_bounds=self._time_bounds,
        )


class TaxRateBuilder:
    """A fluent builder for creating TaxRate instances."""

    def __init__(self, rate: float):
        self._rate = rate
        self._time_bounds: TimeBounds = TimeBounds()

    def with_time_bounds(self, time_bounds: TimeBounds) -> TaxRateBuilder:
        self._time_bounds = time_bounds
        return self

    def build(self) -> TaxRate:
        return TaxRate(rate=self._rate, time_bounds=self._time_bounds)
