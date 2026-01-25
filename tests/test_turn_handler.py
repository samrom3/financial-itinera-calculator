from fitinera.assets import AssetBuilder
from fitinera.cashflows import ExpenseBuilder, IncomeBuilder, TaxRateBuilder
from fitinera.planning import FinancialScenarioBuilder, RetirementGoal, TimeHorizon
from fitinera.core import Age, Month
from fitinera.turn_handler import TurnHandler


def test_single_turn_logic():
    """
    Tests the logic of a single turn calculation.
    """
    time_horizon = TimeHorizon(
        current_age=Age(30, Month.JANUARY), life_expectancy=Age(66, Month.JANUARY)
    )
    retirement_goal = RetirementGoal(retirement_age=Age(65, Month.JANUARY))

    scenario = (
        FinancialScenarioBuilder(name="Data Check", time_horizon=time_horizon)
        .with_asset(AssetBuilder("Savings").with_initial_value(10_000).build())
        .with_income(IncomeBuilder("Job", monthly_amount=5000).build())
        .with_expense(ExpenseBuilder("Rent", monthly_amount=2000).build())
        .with_tax_rate(TaxRateBuilder(0.20).build())
        .with_retirement_goal(retirement_goal)
        .build()
    )

    turn_handler = TurnHandler()
    turn_result, _, _, _ = turn_handler.run(
        scenario,
        scenario.time_horizon.current_age,
        scenario.assets,
        scenario.incomes,
        scenario.expenses,
        scenario.tax_rates,
    )

    assert turn_result.current_age == Age(30, Month.JANUARY)
    assert turn_result.current_asset_breakdown["Savings"] == 10_000
    assert turn_result.next_asset_breakdown["Savings"] == 12_000
    assert turn_result.current_income_breakdown.total == 5000
    assert turn_result.tax_breakdown["Income Tax (20.00%)"] == 1000
    assert sum(turn_result.expense_breakdown.values()) == 2000
    assert turn_result.net_cash_flow == 2000
    assert turn_result.total_contributions == 2000


def test_multi_asset_turn_logic():
    """
    Tests a turn with multiple assets with different priorities.
    """
    time_horizon = TimeHorizon(
        current_age=Age(30, Month.JANUARY), life_expectancy=Age(66, Month.JANUARY)
    )
    retirement_goal = RetirementGoal(retirement_age=Age(65, Month.JANUARY))

    scenario = (
        FinancialScenarioBuilder(name="Multi-Asset Test", time_horizon=time_horizon)
        .with_asset(
            AssetBuilder("Asset 1")
            .with_initial_value(10_000)
            .with_contribution_priority(1)
            .build()
        )
        .with_asset(
            AssetBuilder("Asset 2")
            .with_initial_value(5_000)
            .with_contribution_priority(2)
            .build()
        )
        .with_income(IncomeBuilder("Job", monthly_amount=5000).build())
        .with_tax_rate(TaxRateBuilder(0.20).build())
        .with_retirement_goal(retirement_goal)
        .build()
    )

    turn_handler = TurnHandler()
    turn_result, _, _, _ = turn_handler.run(
        scenario,
        scenario.time_horizon.current_age,
        scenario.assets,
        scenario.incomes,
        scenario.expenses,
        scenario.tax_rates,
    )

    # Net cash flow is 4000 (5000 * 0.8). Asset 2 has higher priority.
    asset_1_final = 10_000
    asset_2_final = 5_000 + 4000
    assert turn_result.next_asset_breakdown["Asset 1"] == asset_1_final
    assert turn_result.next_asset_breakdown["Asset 2"] == asset_2_final
