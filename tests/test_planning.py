import pytest

from fitinera.assets import Asset
from fitinera.cashflows import Expense, Income, IncomeKind, TaxRate
from fitinera.core import Age, AnnualGrowth, Month
from fitinera.planning import (
    FinancialScenario,
    FinancialScenarioBuilder,
    RetirementGoal,
    TimeHorizon,
)


def test_time_horizon_post_init_valid():
    time_horizon = TimeHorizon(
        current_age=Age(30, Month.JANUARY), life_expectancy=Age(95, Month.JANUARY)
    )
    assert time_horizon.current_age == Age(30, Month.JANUARY)
    assert time_horizon.life_expectancy == Age(95, Month.JANUARY)


def test_time_horizon_post_init_invalid():
    with pytest.raises(
        ValueError, match="Current age must be less than life expectancy."
    ):
        TimeHorizon(
            current_age=Age(95, Month.JANUARY), life_expectancy=Age(95, Month.JANUARY)
        )
    with pytest.raises(
        ValueError, match="Current age must be less than life expectancy."
    ):
        TimeHorizon(
            current_age=Age(96, Month.JANUARY), life_expectancy=Age(95, Month.JANUARY)
        )


def test_retirement_goal_post_init_valid():
    retirement_goal = RetirementGoal(
        retirement_age=Age(65, Month.JANUARY), desired_estate_value=1_000_000
    )
    assert retirement_goal.retirement_age == Age(65, Month.JANUARY)
    assert retirement_goal.desired_estate_value == 1_000_000


def test_retirement_goal_post_init_invalid_desired_estate_value():
    with pytest.raises(ValueError, match="Desired estate value cannot be negative."):
        RetirementGoal(retirement_age=Age(65, Month.JANUARY), desired_estate_value=-1)


def test_financial_scenario_post_init_valid():
    time_horizon = TimeHorizon(
        current_age=Age(30, Month.JANUARY), life_expectancy=Age(95, Month.JANUARY)
    )
    retirement_goal = RetirementGoal(retirement_age=Age(65, Month.JANUARY))
    scenario = FinancialScenario(
        name="Test Scenario", time_horizon=time_horizon, retirement_goal=retirement_goal
    )
    assert scenario.name == "Test Scenario"
    assert scenario.time_horizon == time_horizon
    assert scenario.retirement_goal == retirement_goal


def test_financial_scenario_post_init_invalid_name():
    time_horizon = TimeHorizon(
        current_age=Age(30, Month.JANUARY), life_expectancy=Age(95, Month.JANUARY)
    )
    retirement_goal = RetirementGoal(retirement_age=Age(65, Month.JANUARY))
    with pytest.raises(ValueError, match="Name cannot be empty."):
        FinancialScenario(
            name="", time_horizon=time_horizon, retirement_goal=retirement_goal
        )


def test_financial_scenario_post_init_invalid_retirement_age():
    time_horizon = TimeHorizon(
        current_age=Age(30, Month.JANUARY), life_expectancy=Age(95, Month.JANUARY)
    )
    with pytest.raises(
        ValueError,
        match="Retirement age must be between the current age and life expectancy.",
    ):
        FinancialScenario(
            name="Test Scenario",
            time_horizon=time_horizon,
            retirement_goal=RetirementGoal(retirement_age=Age(29, Month.DECEMBER)),
        )
    with pytest.raises(
        ValueError,
        match="Retirement age must be between the current age and life expectancy.",
    ):
        FinancialScenario(
            name="Test Scenario",
            time_horizon=time_horizon,
            retirement_goal=RetirementGoal(retirement_age=Age(95, Month.JANUARY)),
        )


def test_financial_scenario_post_init_duplicate_asset_names():
    time_horizon = TimeHorizon(
        current_age=Age(30, Month.JANUARY), life_expectancy=Age(95, Month.JANUARY)
    )
    retirement_goal = RetirementGoal(retirement_age=Age(65, Month.JANUARY))
    asset1 = Asset(
        name="Duplicate",
        initial_value=1000,
        contribution_priority=1,
        withdrawal_priority=1,
    )
    asset2 = Asset(
        name="Duplicate",
        initial_value=2000,
        contribution_priority=2,
        withdrawal_priority=2,
    )
    with pytest.raises(ValueError, match="Asset names must be unique."):
        FinancialScenario(
            name="Test Scenario",
            time_horizon=time_horizon,
            retirement_goal=retirement_goal,
            assets=[asset1, asset2],
        )


def test_financial_scenario_post_init_duplicate_income_names():
    time_horizon = TimeHorizon(
        current_age=Age(30, Month.JANUARY), life_expectancy=Age(95, Month.JANUARY)
    )
    retirement_goal = RetirementGoal(retirement_age=Age(65, Month.JANUARY))
    income1 = Income(name="Duplicate", monthly_amount=100, kind=IncomeKind.ACTIVE)
    income2 = Income(name="Duplicate", monthly_amount=200, kind=IncomeKind.PASSIVE)
    with pytest.raises(ValueError, match="Income names must be unique."):
        FinancialScenario(
            name="Test Scenario",
            time_horizon=time_horizon,
            retirement_goal=retirement_goal,
            incomes=[income1, income2],
        )


def test_financial_scenario_post_init_duplicate_expense_names():
    time_horizon = TimeHorizon(
        current_age=Age(30, Month.JANUARY), life_expectancy=Age(95, Month.JANUARY)
    )
    retirement_goal = RetirementGoal(retirement_age=Age(65, Month.JANUARY))
    expense1 = Expense(name="Duplicate", monthly_amount=50)
    expense2 = Expense(name="Duplicate", monthly_amount=100)
    with pytest.raises(ValueError, match="Expense names must be unique."):
        FinancialScenario(
            name="Test Scenario",
            time_horizon=time_horizon,
            retirement_goal=retirement_goal,
            expenses=[expense1, expense2],
        )


def test_financial_scenario_builder():
    time_horizon = TimeHorizon(
        current_age=Age(30, Month.JANUARY), life_expectancy=Age(95, Month.JANUARY)
    )
    retirement_goal = RetirementGoal(retirement_age=Age(65, Month.JANUARY))
    asset = Asset(
        name="Test Asset",
        initial_value=1000,
        growth_strategy=AnnualGrowth(0.05, Month.JANUARY),
        contribution_priority=1,
        withdrawal_priority=1,
    )
    income = Income(
        name="Test Income",
        monthly_amount=100,
        kind=IncomeKind.ACTIVE,
        growth_strategy=AnnualGrowth(0.02, Month.JANUARY),
    )
    expense = Expense(
        name="Test Expense",
        monthly_amount=50,
        growth_strategy=AnnualGrowth(0.01, Month.JANUARY),
    )
    tax_rate = TaxRate(rate=0.2)

    scenario = (
        FinancialScenarioBuilder(name="Test Scenario", time_horizon=time_horizon)
        .with_retirement_goal(retirement_goal)
        .with_asset(asset)
        .with_income(income)
        .with_expense(expense)
        .with_tax_rate(tax_rate)
        .build()
    )

    assert scenario.name == "Test Scenario"
    assert scenario.time_horizon == time_horizon
    assert scenario.retirement_goal == retirement_goal
    assert scenario.assets == [asset]
    assert scenario.incomes == [income]
    assert scenario.expenses == [expense]
    assert scenario.tax_rates == [tax_rate]


def test_financial_scenario_builder_missing_retirement_goal():
    time_horizon = TimeHorizon(
        current_age=Age(30, Month.JANUARY), life_expectancy=Age(95, Month.JANUARY)
    )
    with pytest.raises(
        ValueError, match="Retirement goal must be set before building the scenario."
    ):
        FinancialScenarioBuilder(
            name="Test Scenario", time_horizon=time_horizon
        ).build()
