# f-Itinera Simulator Library

f-Itinera Simulator is an open source, extensible, and high-quality financial planning simulation library that allows
individuals or CFPs to simulate a wide range of long-term horizons around the most important wealth building resources:
Assets, Liabilities, Transactions, and Time.

Additionally, every simulated scenario provides a common reporting structure enabling comparative analysis across plans
that can help validate or compare a wide variety wealth strategies and plans.

Some common use cases we facilitate include:

- Understanding "how much" and "when" one may retire from their standard job.
- Determining "when" one may retire given a certain savings, ROI, and expense rates.
- Validate strategic fitness by stress-testing over risk vectors (sequence of returns, inflation, etc.).
- Extending to more advanced wealth-building strategies such as rental real estate, business (e.g., side-hustles), or
  some hybrid in between.

> NOTE: f-Itinera stands for "Fiscus Itinera". While not correct latin, this roughly translates to "Fund Trips" in
> english. Our liberal interpretation of this is more like funding your wealth journey, which is at the heart of any
> finanicial plan.

## Quickstart API Examples

```python
from fitinera import (
    Age,
    AnnualGrowth,
    AssetBuilder,
    ContributionConstraint,
    ExpenseBuilder,
    FinancialScenarioBuilder,
    IncomeBuilder,
    Month,
    MonthlyGrowth,
    Penalty,
    Simulator,
    TimeHorizon,
    RetirementGoal,
    TaxRateBuilder,
    TimeBounds,
)

# 1. Define the simulation's time horizon and retirement goals.
time_horizon = TimeHorizon(current_age=Age(30, Month.JANUARY), life_expectancy=Age(95, Month.JANUARY))
retirement_goal = RetirementGoal(
    retirement_age=Age(65, Month.JANUARY), desired_estate_value=1_000_000
)

# 2. Build the financial scenario using a builder pattern.
scenario_builder = FinancialScenarioBuilder(name="Retirement Plan", time_horizon=time_horizon)

scenario = (
    scenario_builder
    # Add a 401k retirement asset
    .with_asset(
        AssetBuilder("401k")
        .with_initial_value(75_000)
        .with_growth_strategy(MonthlyGrowth(annual_rate=0.07))
        .with_contribution_priority(1)
        .with_withdrawal_priority(2)
        .with_contribution_constraint(
            ContributionConstraint(
                effective_monthly_max=23_500 / 12,
                effective_time_bounds=TimeBounds(end=Age(59, Month.JULY)),
            )
        )
        .with_withdrawal_penalty(
            Penalty(rate=0.10, time_bounds=TimeBounds(end=Age(59, Month.JULY)))
        )  # 10% penalty until 59.5
        .build()
    )
    # Add a taxable brokerage asset
    .with_asset(
        AssetBuilder("Taxable Brokerage")
        .with_initial_value(25_000)
        .with_growth_strategy(MonthlyGrowth(annual_rate=0.07))
        .with_contribution_priority(2)
        .with_withdrawal_priority(1)
        .with_withdrawal_tax(
            TaxRateBuilder(0.15).build()
        )  # 15% capital gains tax on withdrawals
        .build()
    )
    # Add an active W2 income stream
    .with_income(
        IncomeBuilder("W2 Income", monthly_amount=6_000)
        .is_active_income()
        .with_growth_strategy(
            AnnualGrowth(annual_rate=0.03, month_of_year=Month.MARCH)
        )  # 3% raise every March
        .with_time_bounds(TimeBounds(end=retirement_goal.retirement_age))
        .build()
    )
    # Add a recurring expense stream
    .with_expense(
        ExpenseBuilder("Living Expenses", monthly_amount=3_500)
        .with_growth_strategy(MonthlyGrowth(annual_rate=0.025))  # 2.5% inflation
        .build()
    )
    # Add a tax strategy
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
    # Set the final retirement goal
    .with_retirement_goal(retirement_goal)
    .build()
)

# 3. Run the simulation and view the results.
simulator = Simulator()
results = simulator.run(scenario)

print(results.summary())
```

## Conceptual Guide

The f-Itinera Simulator is built around a few core concepts that model your financial life. By providing inputs for each
of these, you can create a detailed simulation of your journey to financial independence and retirement.

At a high level, a simulation is defined by four components: a **Financial Scenario**, the **Time Horizon**, your **Assets**, your **Cash Flow**,
and your **Goals**.

### 1. Financial Scenario

The Financial Scenario is the top-level container for a simulation. It bundles together all the components of a
financial plan.

| Parameter         | Type                | Description                                                               |
| ----------------- | ------------------- | ------------------------------------------------------------------------- |
| `name`            | `str`               | A unique name to identify the scenario.                                   |
| `time_horizon`    | `TimeHorizon`       | The time horizon for the simulation.                                      |
| `retirement_goal` | `RetirementGoal`    | The retirement goal for the simulation.                                   |
| `assets`          | `list[Asset]`       | A list of all assets in the scenario.                                     |
| `incomes`         | `list[Income]`      | A list of all income streams in the scenario.                             |
| `expenses`        | `list[Expense]`     | A list of all expense streams in the scenario.                            |
| `tax_rates`       | `list[TaxRate]`     | A list of all tax rates in the scenario.                                  |

### 2. Time Horizon

The Time Horizon defines the duration and key milestones of the simulation. It is the foundational context for all
events.

| Parameter         | Type  | Description                                             |
| ----------------- | ----- | ------------------------------------------------------- |
| `current_age`     | `Age` | The starting age of the subject of the simulation.      |
| `life_expectancy` | `Age` | The end point of the simulation (default is 100 years). |

### 3. Retirement Goals

This defines the primary objective of the simulation: achieving retirement.

| Parameter              | Type    | Description                                                                                                 |
| ---------------------- | ------- | ----------------------------------------------------------------------------------------------------------- |
| `retirement_age`       | `Age`   | The age you plan to stop working. This is a key milestone for the simulation.                               |
| `desired_estate_value` | `float` | Optional (default: 0). The desired minimum total asset value you wish to have at the end of the simulation. |

> **IMPORTANT**: The retirement age must be equal to or greater than the starting age and strictly less than the life
> expectancy.

### 4. Assets & Investments

Assets represent your current and future investments that you can live off of. You can add multiple asset accounts to a
simulation.

| Parameter                  | Type                                | Description                                                                                                                        |
| -------------------------- | ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `name`                     | `str`                               | A unique name that identifies the account/asset.                                                                                   |
| `initial_value`            | `float`                             | The starting value of the asset.                                                                                                   |
| `growth_strategy`          | `GrowthStrategy`                    | The compounding growth rate of the asset. See [Core Data Types](#6-core-data-types).                                               |
| `contribution_priority`    | `int`                               | A positive integer indicating the preference to contribute extra net cash flow to this asset. Higher numbers have higher priority. |
| `withdrawal_priority`      | `int`                               | A positive integer indicating the preference to withdraw from this asset to cover deficits. Higher numbers have higher priority.   |
| `contribution_constraints` | `list[ContributionConstraint]` | Optional. A list of constraints that limit how much can be contributed to this asset.                                              |
| `withdrawal_penalties`     | `list[Penalty]`                     | Optional. A list of penalties applied to withdrawals, useful for modeling early withdrawal from tax-advantaged accounts.           |
| `withdrawal_taxes`         | `list[TaxRate]`                     | Optional. A list of tax rates applied to withdrawals, useful for modeling capital gains or income tax on withdrawals.            |

#### 4.1. Contribution Constraints

You can apply one or more constraints to an asset to model contribution limits, such as annual 401(k) or IRA maximums.

| Parameter                 | Type         | Description                                                                          |
| ------------------------- | ------------ | ------------------------------------------------------------------------------------ |
| `effective_time_bounds`   | `TimeBounds` | Optional. The time range when this constraint is in effect.                          |
| `effective_monthly_max`   | `float`      | The maximum that can be contributed monthly during the specified time range.         |

#### 4.2. Withdrawal Penalties

Withdrawal penalties can be used to model early withdrawal fees from tax-advantaged accounts.

| Parameter     | Type         | Description                                                                  |
| ------------- | ------------ | ---------------------------------------------------------------------------- |
| `rate`        | `float`      | The penalty rate, expressed as a decimal between 0.0 and 1.0.                |
| `time_bounds` | `TimeBounds` | The time range when this penalty is in effect.                               |

### 5. Cash Flow

Cash Flow models the money moving in and out of your accounts over the course of the simulation. It is composed of
income, taxes, and expenses.

#### 5.1. Income Streams

You can add any number of income sources. The `kind` of income is critical for determining financial independence.

| Parameter         | Type             | Description                                                                                               |
| ----------------- | ---------------- | --------------------------------------------------------------------------------------------------------- |
| `name`            | `str`            | A unique name for the income stream.                                                                      |
| `monthly_amount`  | `float`          | The initial monthly amount received.                                                                      |
| `time_bounds`     | `TimeBounds`     | The time range when this income is active. See [Core Data Types](#6-core-data-types).                     |
| `kind`            | `IncomeKind`     | `ACTIVE` or `PASSIVE`. Passive income counts towards financial independence goals.                        |
| `growth_strategy` | `GrowthStrategy` | The rate at which the income changes over time (e.g., raises). See [Core Data Types](#6-core-data-types). |

#### 5.2. Expense Streams

You can add any number of after-tax expense sources.

| Parameter         | Type             | Description                                                                                                   |
| ----------------- | ---------------- | ------------------------------------------------------------------------------------------------------------- |
| `name`            | `str`            | A unique name for the expense stream.                                                                         |
| `monthly_amount`  | `float`          | The initial monthly amount spent.                                                                             |
| `time_bounds`     | `TimeBounds`     | The time range when this expense is active. See [Core Data Types](#6-core-data-types).                        |
| `growth_strategy` | `GrowthStrategy` | The rate at which the expense changes over time (i.e., inflation). See [Core Data Types](#6-core-data-types). |

#### 5.3. Tax Rates

Tax rates are applied to your gross income each month. You can specify different rates for different periods (e.g., pre-
and post-retirement).

| Parameter     | Type         | Description                                                                                |
| ------------- | ------------ | ------------------------------------------------------------------------------------------ |
| `rate`        | `float`      | A decimal between \[0.0, 1.0) representing the effective tax rate.                         |
| `time_bounds` | `TimeBounds` | The time range when this tax rate is in effect. See [Core Data Types](#6-core-data-types). |

#### 5.4. One-Time Payments

The simulator allows for modeling one-off lump sum payments (positive for income, negative for expenses).

| Parameter | Type    | Description                           |
| --------- | ------- | ------------------------------------- |
| `amount`  | `float` | The value of the payment.             |
| `age`     | `Age`   | The age at which this payment occurs. |

### 6. The Simulation Lifecycle

The simulator executes on a month-by-month loop. For each month, the following operations are executed in order:

1. **Check Retirement Status**: Determine if the subject's age has reached the `retirement_age` milestone.
1. **Compute Gross Income**: Sum all active income streams for the current month.
1. **Apply Taxes**: Apply the relevant tax rate to the gross income to calculate net income.
1. **Aggregate Expenses**: Sum all active expense streams for the current month.
1. **Calculate Net Cash Flow**: Compute `Net Income - Expenses`.
1. **Apply Asset Flows**:
   - If Net Cash Flow is **positive**, deposit the surplus into assets based on their `contribution_priority`.
   - If Net Cash Flow is **negative**, withdraw the deficit from assets based on their `withdrawal_priority`.
1. **Check State**: Assess the simulation for end conditions (see below).
1. **Compound Values**: Apply the `growth_strategy` to all assets, income streams, and expenses to prepare for the next
   month.

The simulation concludes when one of the following conditions is met:

- **Pre-Retirement Bankruptcy (Failure)**: Assets are depleted before reaching retirement age.
- **Post-Retirement Bankruptcy (Failure)**: Assets are depleted after retirement age but before life expectancy.
- **Insufficient Estate (Partial Success)**: Life expectancy is reached, but the final asset value is less than the
  `desired_estate_value`.
- **Success**: Life expectancy is reached with sufficient assets to meet the estate goal.

#### 6.1. Simulation Results

The `simulator.run()` method returns a `SimulationResult` object that contains the final status of the simulation and a
detailed history of each time step.

| Parameter | Type                  | Description                                                                    |
| --------- | --------------------- | ------------------------------------------------------------------------------ |
| `status`  | `SimulationStatus`    | The final status of the simulation (e.g., `SUCCESS`, `PRE_RETIREMENT_BANKRUPTCY`). |
| `history` | `list[SimulationTurn]` | A list of `SimulationTurn` objects, one for each month of the simulation.      |
| `scenario`| `FinancialScenario`   | The original financial scenario that was simulated.                            |

Each `SimulationTurn` object provides a detailed breakdown of the financial state for a single month, including income,
expenses, taxes, asset growth, and key metrics like the financial freedom ratio and savings rate.

### 7. Core Data Types

These are the common, low-level data structures used to configure the concepts above.

#### 7.1. Age and TimeBounds

The simulator models time based on the subject's age, specified with a `Year` and `Month`. The `Month` is a strongly-
typed enum to prevent invalid month values. Most entities use a `TimeBounds` object to define when they are active.

- **`Age(year: int, month: Month)`**: Represents a specific point in time (e.g., `Age(65, Month.JANUARY)`).
- **`TimeBounds(start: Age | RetirementGoal, end: Age | RetirementGoal)`**: Defines a time range. The `start` and `end`
  can be a specific `Age` or can be relative to the `RetirementGoal`. A `None` value means the start or end of the
  simulation.

#### 7.2. Growth Strategy

This interface models how values change over time.

- **`Monthly(annual_rate: float)`**: The preferred and simplest method. The value compounds each month by
  `annual_rate / 12`.
- **`Annual(annual_rate: float, month_of_year: Month)`**: The value compounds once per year in the specified `Month`.

Here are some common rules of thumb:

- Most `ACTIVE` incomes should be modeled with `Annual` growth (representing an annual raise).
- Most `PASSIVE` incomes and `Expenses` should be modeled with `Monthly` growth.

## License

All code contained in this repositoriy is licensed under GPL-v3.
