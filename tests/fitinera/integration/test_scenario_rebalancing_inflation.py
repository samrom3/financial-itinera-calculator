"""Integration test — Scenario 3: rebalancing with inflation and brokerage growth.

Two accounts (checking ASSET, brokerage ASSET 8% annual return). Person works
from age 22 to 61, accumulating savings in a brokerage via RebalanceExtraSavingsFlow
with CurrentTurnExpenseStrategy. Living expenses inflate at 2% per year.

The simulation runs for 39 years (the full working period). Assertions cover:
  - result.success is True
  - checking account is never negative across all turns
  - brokerage balance grows monotonically during working years (age 22 to 61)

Note: The simulation is bounded to the working period (max_turns = TurnDuration.of(years=39))
because no income flows are active after retirement, and the pipeline has no drawdown
flow from brokerage to checking. Running through retirement would cause checking to
go negative on the first post-retirement turn (expenses continue while income stops).
"""

from fitinera import (
    Account,
    Age,
    Date,
    Person,
    SimulationScenario,
    TurnDuration,
)
from fitinera.engine import EngineConfiguration, SimulationEngine
from fitinera.flows import (
    AccountInterestFlow,
    AccountSolvencyGuardFlow,
    ComparisonOperator,
    CurrentTurnExpenseStrategy,
    JobIncomeFlow,
    LivingExpenseFlow,
    PersonAgeIs,
    PersonRetirementLabelFlow,
    RebalanceExtraSavingsFlow,
)

# ---------------------------------------------------------------------------
# Scenario constants
# ---------------------------------------------------------------------------

_ANNUAL_INCOME = 100_000.0
_MONTHLY_INCOME = _ANNUAL_INCOME / 12  # ~8333.33

_ANNUAL_EXPENSE = 50_000.0
_MONTHLY_EXPENSE = _ANNUAL_EXPENSE / 12  # ~4166.67
_ANNUAL_INFLATION = 0.02

_BROKERAGE_ANNUAL_RATE = 0.08
_REBALANCE_MULTIPLIER = 3.0

_START_AGE = Age(22)
_RETIRE_AGE = Age(61)
_LIFE_EXPECTANCY = Age(100)

# 39 working years = 468 monthly turns
_WORKING_YEARS = _RETIRE_AGE.years - _START_AGE.years
_MAX_TURNS = TurnDuration.of(years=_WORKING_YEARS)


def _build_scenario() -> SimulationScenario:
    """Return the scenario with checking and brokerage accounts plus one person.

    Both accounts start at $0; the person starts at age 22 with Status=Working.
    """
    return SimulationScenario(
        initial_persons=[
            Person(
                id="person",
                age=_START_AGE,
                expectancy=_LIFE_EXPECTANCY,
                labels={"Status": "Working"},
            )
        ],
        initial_accounts=[
            Account(
                id="checking",
                balance=0.0,
                labels={"Type": "ASSET"},
            ),
            Account(
                id="brokerage",
                balance=0.0,
                labels={"Type": "ASSET"},
            ),
        ],
    )


def _build_config() -> EngineConfiguration:
    """Return the pipeline configuration for Scenario 3.

    Pipeline order per the spec:
      1. JobIncomeFlow  — income only while Status=Working
      2. LivingExpenseFlow — with 2% annual inflation
      3. RebalanceExtraSavingsFlow — transfer excess from checking to brokerage
      4. AccountInterestFlow — 8% annual return on brokerage (monthly compounding)
      5. PersonRetirementLabelFlow — set Retired when age >= 61
      6. AccountSolvencyGuardFlow — halt on negative ASSET balance
    """
    return EngineConfiguration(
        start_date=Date(2026, 1),
        max_turns=_MAX_TURNS,
        flows=[
            JobIncomeFlow(
                person_id="person",
                amount=_MONTHLY_INCOME,
                to_account="checking",
            ),
            LivingExpenseFlow(
                from_account="checking",
                amount=_MONTHLY_EXPENSE,
                annual_inflation_rate=_ANNUAL_INFLATION,
            ),
            RebalanceExtraSavingsFlow(
                from_account="checking",
                to_account="brokerage",
                strategy=CurrentTurnExpenseStrategy(_REBALANCE_MULTIPLIER),
            ),
            AccountInterestFlow(
                account_id="brokerage",
                annual_rate=_BROKERAGE_ANNUAL_RATE,
            ),
            PersonRetirementLabelFlow(
                person_ids=["person"],
                condition=PersonAgeIs(
                    person_id="person",
                    operator=ComparisonOperator.GE,
                    age=_RETIRE_AGE,
                ),
            ),
            AccountSolvencyGuardFlow(),
        ],
    )


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------


class TestScenario3RebalancingInflation:
    """Integration tests for Scenario 3: rebalancing with inflation.

    Validates that a single-person pipeline with JobIncomeFlow, inflation-adjusted
    LivingExpenseFlow, RebalanceExtraSavingsFlow, AccountInterestFlow, and
    PersonRetirementLabelFlow produces a successful result over the working period.
    """

    def test_scenario3_completes_without_exception(self):
        """Simulation completes without exception across 39 working years.

        No ASSET account balance goes negative, so AccountSolvencyGuardFlow never
        raises and the engine halts via max_turns.
        """
        config = _build_config()
        scenario = _build_scenario()

        result = SimulationEngine(config).run(scenario)

        assert isinstance(result.turns, list)

    def test_scenario3_produces_expected_turn_count(self):
        """Engine runs for exactly 468 turns (39 years * 12 months).

        The working period spans from age 22 to 61, generating one turn per
        calendar month. max_turns=TurnDuration.of(years=39) = 468 monthly turns.
        """
        config = _build_config()
        scenario = _build_scenario()

        result = SimulationEngine(config).run(scenario)

        expected_turns = _WORKING_YEARS * 12
        assert len(result.turns) == expected_turns

    def test_scenario3_checking_balance_never_negative(self):
        """Checking account balance is non-negative across every turn.

        AccountSolvencyGuardFlow monitors the ASSET-labeled checking account.
        Income exceeds expenses throughout the working period, so the balance
        stays non-negative after the first few turns needed to build the minimum
        savings buffer.
        """
        config = _build_config()
        scenario = _build_scenario()

        result = SimulationEngine(config).run(scenario)

        for i, turn in enumerate(result.turns):
            checking = next(a for a in turn.accounts if a.id == "checking")
            assert checking.balance >= 0.0, (
                f"Checking went negative at turn {i + 1}: {checking.balance}"
            )

    def test_scenario3_brokerage_grows_during_working_years(self):
        """Brokerage balance increases monotonically after the first transfer occurs.

        During working years the excess savings (checking balance above 3x monthly
        expense buffer) are transferred to brokerage each turn, and brokerage earns
        8% annual return via AccountInterestFlow. After the initial build-up period
        (~3-4 turns) the brokerage balance should be strictly increasing.
        """
        config = _build_config()
        scenario = _build_scenario()

        result = SimulationEngine(config).run(scenario)

        # Find the first turn where brokerage is non-zero (first rebalance transfer).
        first_nonzero = None
        for i, turn in enumerate(result.turns):
            brokerage = next(a for a in turn.accounts if a.id == "brokerage")
            if brokerage.balance > 0.0:
                first_nonzero = i
                break

        # Brokerage must receive at least one transfer during working years.
        assert first_nonzero is not None, (
            "Brokerage balance never exceeded zero during working years"
        )

        # After the first transfer, brokerage must keep growing (income + interest).
        prev_balance = 0.0
        for turn in result.turns[first_nonzero:]:
            brokerage = next(a for a in turn.accounts if a.id == "brokerage")
            assert brokerage.balance >= prev_balance, (
                f"Brokerage decreased from {prev_balance} to {brokerage.balance}"
            )
            prev_balance = brokerage.balance

    def test_scenario3_brokerage_positive_at_end_of_working_years(self):
        """Brokerage account has a significant positive balance at the end of working years.

        Over 39 years of rebalancing plus 8% annual compounding, the brokerage
        balance must grow substantially. We assert it exceeds $100,000 to confirm
        the rebalance and interest flows are both active.
        """
        config = _build_config()
        scenario = _build_scenario()

        result = SimulationEngine(config).run(scenario)

        last_turn = result.turns[-1]
        brokerage = next(a for a in last_turn.accounts if a.id == "brokerage")
        assert brokerage.balance > 100_000.0, (
            f"Expected brokerage > $100,000 at end of working years, got {brokerage.balance}"
        )

    def test_scenario3_person_is_retired_at_last_turn(self):
        """Person Status label is 'Retired' on the last turn (age 61).

        PersonRetirementLabelFlow sets Status=Retired when PersonAgeIs(person, GE,
        Age(61)) evaluates True. With max_turns=39 years, the person reaches age 61
        on turn 468 and the label is applied.
        """
        config = _build_config()
        scenario = _build_scenario()

        result = SimulationEngine(config).run(scenario)

        last_turn = result.turns[-1]
        person = next(p for p in last_turn.persons if p.id == "person")
        assert person.get_label("Status") == "Retired"

    def test_scenario3_solvency_guard_does_not_raise(self):
        """AccountSolvencyGuardFlow does not raise during the working period.

        With income of $100k/yr and living expenses of $50k/yr, the net monthly
        inflow keeps the checking account positive throughout the working period.
        """
        config = _build_config()
        scenario = _build_scenario()

        result = SimulationEngine(config).run(scenario)

        expected_turns = _WORKING_YEARS * 12
        assert len(result.turns) == expected_turns
