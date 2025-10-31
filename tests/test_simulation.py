from fitinera.assets import AssetBuilder
from fitinera.cashflows import ExpenseBuilder, IncomeBuilder, TaxRateBuilder
from fitinera.planning import FinancialScenarioBuilder, RetirementGoal, TimeHorizon
from fitinera.results import SimulationStatus
from fitinera.simulation import Simulator
from fitinera.core import Age, Month, TimeBounds, MonthlyGrowth


def test_simulator_success_scenario():
    """
    Tests a simulation that should result in a successful retirement.
    """
    # 1. Define the simulation's time horizon and retirement goals.
    time_horizon = TimeHorizon(current_age=Age(30, Month.JANUARY), life_expectancy=Age(95, Month.JANUARY))
    retirement_goal = RetirementGoal(
        retirement_age=Age(65, Month.JANUARY), desired_estate_value=1_000_000
    )

    # 2. Build the financial scenario.
    scenario = (
        FinancialScenarioBuilder(name="Retirement Plan", time_horizon=time_horizon)
        .with_asset(
            AssetBuilder("401k")
            .with_initial_value(75_000)
            .with_contribution_priority(1)
            .with_withdrawal_priority(1)
            .with_growth_strategy(MonthlyGrowth(annual_rate=0.07))
            .build()
        )
        .with_income(
            IncomeBuilder("W2 Income", monthly_amount=6_000)
            .with_time_bounds(TimeBounds(end=retirement_goal.retirement_age))
            .build()
        )
        .with_expense(
            ExpenseBuilder("Living Expenses", monthly_amount=3_500)
            .build()
        )
        .with_tax_rate(
            TaxRateBuilder(0.22)
            .with_time_bounds(TimeBounds(end=retirement_goal.retirement_age))
            .build()
        )
        .with_tax_rate(
            TaxRateBuilder(0.12)
            .with_time_bounds(TimeBounds(start=retirement_goal.retirement_age))
            .build()
        )
        .with_retirement_goal(retirement_goal)
        .build()
    )

    # 3. Run the simulation.
    simulator = Simulator()
    results = simulator.run(scenario)

    # 4. Assert the results.
    assert results.status == SimulationStatus.SUCCESS
    assert len(results.history) > 0


def test_simulator_pre_retirement_bankruptcy_scenario():
    """
    Tests a simulation that should result in pre-retirement bankruptcy.
    """
    time_horizon = TimeHorizon(current_age=Age(30, Month.JANUARY), life_expectancy=Age(95, Month.JANUARY))
    retirement_goal = RetirementGoal(retirement_age=Age(65, Month.JANUARY))

    scenario = (
        FinancialScenarioBuilder(name="Bankruptcy Plan", time_horizon=time_horizon)
        .with_asset(AssetBuilder("Savings").with_initial_value(1000).build())
        .with_expense(ExpenseBuilder("High Expenses", monthly_amount=5000).build())
        .with_retirement_goal(retirement_goal)
        .build()
    )

    simulator = Simulator()
    results = simulator.run(scenario)

    assert results.status == SimulationStatus.PRE_RETIREMENT_BANKRUPTCY


def test_simulator_post_retirement_bankruptcy_scenario():
    """
    Tests a simulation that should result in post-retirement bankruptcy.
    """
    time_horizon = TimeHorizon(current_age=Age(65, Month.JANUARY), life_expectancy=Age(95, Month.JANUARY))
    retirement_goal = RetirementGoal(retirement_age=Age(65, Month.JANUARY))

    scenario = (
        FinancialScenarioBuilder(name="Post-Retirement Bankruptcy", time_horizon=time_horizon)
        .with_asset(AssetBuilder("Retirement Fund").with_initial_value(100_000).build())
        .with_expense(ExpenseBuilder("High Retirement Expenses", monthly_amount=5000).build())
        .with_retirement_goal(retirement_goal)
        .build()
    )

    simulator = Simulator()
    results = simulator.run(scenario)

    assert results.status == SimulationStatus.POST_RETIREMENT_BANKRUPTCY


def test_simulator_insufficient_estate_scenario():
    """
    Tests a simulation that should result in an insufficient estate.
    """
    time_horizon = TimeHorizon(current_age=Age(65, Month.JANUARY), life_expectancy=Age(95, Month.JANUARY))
    retirement_goal = RetirementGoal(
        retirement_age=Age(65, Month.JANUARY), desired_estate_value=1_000_000
    )

    scenario = (
        FinancialScenarioBuilder(name="Insufficient Estate", time_horizon=time_horizon)
        .with_asset(AssetBuilder("Retirement Fund").with_initial_value(100_000).build())
        .with_retirement_goal(retirement_goal)
        .build()
    )

    simulator = Simulator()
    results = simulator.run(scenario)

    assert results.status == SimulationStatus.INSUFFICIENT_ESTATE


def test_simulation_turn_data():
    """
    Tests that the data within a SimulationTurn is calculated correctly.
    """
    time_horizon = TimeHorizon(current_age=Age(30, Month.JANUARY), life_expectancy=Age(66, Month.JANUARY))
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

    simulator = Simulator()
    results = simulator.run(scenario)
    turn = results.history[0]

    assert turn.current_age == Age(30, Month.JANUARY)
    assert turn.total_assets == 12_000
    assert turn.income_breakdown.total == 5000
    assert turn.tax_breakdown["Income Tax (20.00%)"] == 1000
    assert turn.total_expenses == 2000
    assert turn.net_cash_flow == 2000
    assert turn.total_contributions == 2000


def test_multi_asset_scenario():
    """
    Tests a scenario with multiple assets with different priorities.
    """
    time_horizon = TimeHorizon(current_age=Age(30, Month.JANUARY), life_expectancy=Age(66, Month.JANUARY))
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

    simulator = Simulator()
    results = simulator.run(scenario)
    turn = results.history[0]

    # Net cash flow is 4000 (5000 * 0.8). Asset 2 has higher priority.
    asset_1_final = 10_000
    asset_2_final = 5_000 + 4000
    assert turn.total_assets == asset_1_final + asset_2_final
