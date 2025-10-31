from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING

# This block is only for type hinting and is not executed at runtime.
# It prevents circular imports between the simulation and planning modules.
if TYPE_CHECKING:
    from .planning import FinancialScenario
    from .core import Age


class SimulationStatus(Enum):
    """The final status of a financial simulation."""

    SUCCESS = auto()
    """Life expectancy is reached with sufficient assets to meet the estate goal."""

    INSUFFICIENT_ESTATE = auto()
    """Life expectancy is reached, but the final asset value is less than the desired_estate_value."""

    POST_RETIREMENT_BANKRUPTCY = auto()
    """Assets are depleted after retirement age but before life expectancy."""

    PRE_RETIREMENT_BANKRUPTCY = auto()
    """Assets are depleted before reaching retirement age."""


@dataclass(frozen=True)
class GrowthApplication:
    """
    Represents the application of a growth strategy to a single entity in a single turn.
    """

    name: str
    rate: float
    """The selected growth rate from the configuration."""
    amount: float


@dataclass(frozen=True)
class IncomeBreakdown:
    """Breakdown of income for a single simulation turn."""

    active: dict[str, float] = field(default_factory=dict)
    passive: dict[str, float] = field(default_factory=dict)

    @property
    def total_active(self) -> float:
        """The total active income for a given turn."""
        return sum(self.active.values())

    @property
    def total_passive(self) -> float:
        """The total passive income for a given turn."""
        return sum(self.passive.values())

    @property
    def total(self) -> float:
        """The total income for a given turn."""
        return self.total_active + self.total_passive


@dataclass(frozen=True)
class SimulationTurn:
    """Represents the financial state at a single time step (month) in the simulation."""

    current_age: Age
    net_cash_flow: float

    # Breakdowns
    current_asset_breakdown: dict[str, float] = field(default_factory=dict)
    next_asset_breakdown: dict[str, float] = field(default_factory=dict)
    current_income_breakdown: IncomeBreakdown = field(default_factory=IncomeBreakdown)
    next_income_breakdown: IncomeBreakdown = field(default_factory=IncomeBreakdown)
    total_contributions: float = 0.0
    withdrawal_breakdown: dict[str, float] = field(default_factory=dict)
    total_penalties: float = 0.0
    expense_breakdown: dict[str, float] = field(default_factory=dict)
    tax_breakdown: dict[str, float] = field(default_factory=dict)
    asset_growth_breakdown: list[GrowthApplication] = field(default_factory=list)
    income_growth_breakdown: list[GrowthApplication] = field(default_factory=list)
    expense_growth_breakdown: list[GrowthApplication] = field(default_factory=list)

    @property
    def total_current_assets(self) -> float:
        """The total assets at the beginning of the turn."""
        return sum(self.current_asset_breakdown.values())

    @property
    def total_next_assets(self) -> float:
        """The total assets at the end of the turn."""
        return sum(self.next_asset_breakdown.values())

    @property
    def total_current_income(self) -> float:
        """The total income at the beginning of the turn."""
        return self.current_income_breakdown.total

    @property
    def total_next_income(self) -> float:
        """The total income at the end of the turn."""
        return self.next_income_breakdown.total

    @property
    def total_expenses(self) -> float:
        """The total expenses for a given turn."""
        return sum(self.expense_breakdown.values())

    @property
    def total_asset_growth(self) -> float:
        """The total asset growth for a given turn."""
        return sum(growth.amount for growth in self.asset_growth_breakdown)

    @property
    def total_income_growth(self) -> float:
        """The total income growth for a given turn."""
        return sum(growth.amount for growth in self.income_growth_breakdown)

    @property
    def financial_freedom_ratio(self) -> float:
        """Ratio of passive income and asset growth to total expenses."""
        if self.total_expenses == 0:
            return float("inf")
        return (
            self.current_income_breakdown.total_passive + self.total_asset_growth
        ) / self.total_expenses

    @property
    def savings_rate(self) -> float:
        """Ratio of contributions to total income."""
        if self.total_current_income == 0:
            return 0.0
        return self.total_contributions / self.total_current_income

    @property
    def expense_ratio(self) -> float:
        """Ratio of expenses to income."""
        if self.total_current_income == 0:
            return float("inf")
        return self.total_expenses / self.total_current_income

    @property
    def income_growth_ratio(self) -> float:
        """Ratio of income growth to current income."""
        if self.total_current_income == 0:
            return 0.0
        return self.total_income_growth / self.total_current_income


@dataclass(frozen=True)
class SimulationResult:
    """The final result of a financial simulation."""

    status: SimulationStatus
    history: list[SimulationTurn]
    scenario: FinancialScenario
