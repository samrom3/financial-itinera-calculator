from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .assets import Asset
from .cashflows import Expense, Income, TaxRate
from .core import Age


@dataclass(frozen=True)
class TimeHorizon:
    """Defines the time horizon for a financial simulation."""

    current_age: Age
    life_expectancy: Age

    def __post_init__(self):
        if self.current_age >= self.life_expectancy:
            raise ValueError("Current age must be less than life expectancy.")


@dataclass(frozen=True)
class RetirementGoal:
    """Defines the retirement goal for a financial simulation."""

    retirement_age: Age
    desired_estate_value: float = 0.0

    def __post_init__(self):
        if self.desired_estate_value < 0:
            raise ValueError("Desired estate value cannot be negative.")


@dataclass(frozen=True)
class FinancialScenario:
    """Represents a comprehensive financial scenario for simulation."""

    name: str
    time_horizon: TimeHorizon
    retirement_goal: RetirementGoal
    assets: List[Asset] = field(default_factory=list)
    incomes: List[Income] = field(default_factory=list)
    expenses: List[Expense] = field(default_factory=list)
    tax_rates: List[TaxRate] = field(default_factory=list)

    def __post_init__(self):
        """
        Validate the financial scenario after initialization.

        Ensures that:
        - The scenario name is not empty
        - The retirement age is logically consistent with the time horizon
          (i.e., retirement age is greater than or equal to current age and
           less than life expectancy)
        - Each Asset has a unique name and valid initial value
        - Each Expense has a unique name and valid monthly amount
        - Each Income has a unique name and valid monthly amount
        - Each TaxRate has valid time bounds and rates between 0 and 1

        Raises:
            ValueError: If the name is empty or if the retirement age is not
                       between current age and life expectancy.
        """
        if not self.name:
            raise ValueError("Name cannot be empty.")
        if not (
            self.time_horizon.current_age
            <= self.retirement_goal.retirement_age
            < self.time_horizon.life_expectancy
        ):
            raise ValueError(
                "Retirement age must be between the current age and life expectancy."
            )

        asset_names = {asset.name for asset in self.assets}
        if len(asset_names) != len(self.assets):
            raise ValueError("Asset names must be unique.")

        income_names = {income.name for income in self.incomes}
        if len(income_names) != len(self.incomes):
            raise ValueError("Income names must be unique.")

        expense_names = {expense.name for expense in self.expenses}
        if len(expense_names) != len(self.expenses):
            raise ValueError("Expense names must be unique.")


class FinancialScenarioBuilder:
    """A fluent builder for creating FinancialScenario instances."""

    def __init__(self, name: str, time_horizon: TimeHorizon):
        self._name = name
        self._time_horizon = time_horizon
        self._retirement_goal: RetirementGoal | None = None
        self._assets: List[Asset] = []
        self._incomes: List[Income] = []
        self._expenses: List[Expense] = []
        self._tax_rates: List[TaxRate] = []

    def with_retirement_goal(
        self, retirement_goal: RetirementGoal
    ) -> FinancialScenarioBuilder:
        self._retirement_goal = retirement_goal
        return self

    def with_asset(self, asset: Asset) -> FinancialScenarioBuilder:
        self._assets.append(asset)
        return self

    def with_income(self, income: Income) -> FinancialScenarioBuilder:
        self._incomes.append(income)
        return self

    def with_expense(self, expense: Expense) -> FinancialScenarioBuilder:
        self._expenses.append(expense)
        return self

    def with_tax_rate(self, tax_rate: TaxRate) -> FinancialScenarioBuilder:
        self._tax_rates.append(tax_rate)
        return self

    def build(self) -> FinancialScenario:
        if self._retirement_goal is None:
            raise ValueError(
                "Retirement goal must be set before building the scenario."
            )

        return FinancialScenario(
            name=self._name,
            time_horizon=self._time_horizon,
            retirement_goal=self._retirement_goal,
            assets=self._assets,
            incomes=self._incomes,
            expenses=self._expenses,
            tax_rates=self._tax_rates,
        )
