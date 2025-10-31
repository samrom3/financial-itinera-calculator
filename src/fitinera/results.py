from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .planning import FinancialScenario
    from .core import Age


class SimulationStatus(Enum):
    """The final status of a financial simulation."""

    SUCCESS = auto()
    INSUFFICIENT_ESTATE = auto()
    POST_RETIREMENT_BANKRUPTCY = auto()
    PRE_RETIREMENT_BANKRUPTCY = auto()


@dataclass(frozen=True)
class GrowthApplication:
    """Represents the application of a growth strategy to a single entity."""

    name: str
    rate: float
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
    total_assets: float

    # Breakdowns
    income_breakdown: IncomeBreakdown

    # Cash Flow
    net_cash_flow: float
    total_contributions: float
    total_withdrawals: float
    total_penalties: float

    # Breakdowns with defaults
    expense_breakdown: dict[str, float] = field(default_factory=dict)
    tax_breakdown: dict[str, float] = field(default_factory=dict)
    asset_growth_breakdown: list[GrowthApplication] = field(default_factory=list)
    income_growth_breakdown: list[GrowthApplication] = field(default_factory=list)
    expense_growth_breakdown: list[GrowthApplication] = field(default_factory=list)

    @property
    def total_expenses(self) -> float:
        """The total expenses for a given turn."""
        return sum(self.expense_breakdown.values())

    @property
    def total_asset_growth(self) -> float:
        """The total asset growth for a given turn."""
        return sum(growth.amount for growth in self.asset_growth_breakdown)

    @property
    def financial_freedom_ratio(self) -> float:
        """Ratio of total expenses to passive income and asset growth."""
        passive_income_and_growth = (
            self.income_breakdown.total_passive + self.total_asset_growth
        )
        if passive_income_and_growth == 0:
            return 0.0
        return self.total_expenses / passive_income_and_growth

    @property
    def savings_rate(self) -> float:
        """Ratio of contributions to total income."""
        if self.income_breakdown.total == 0:
            return 0.0
        return self.total_contributions / self.income_breakdown.total


@dataclass(frozen=True)
class SimulationResult:
    """The final result of a financial simulation."""

    status: SimulationStatus
    history: list[SimulationTurn]
    scenario: FinancialScenario
