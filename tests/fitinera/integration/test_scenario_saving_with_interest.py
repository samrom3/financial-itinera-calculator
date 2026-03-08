"""Integration test: Scenario 2 — Saving with compound interest.

This scenario is identical to Scenario 1 (simple saving) with the addition of
AccountInterestFlow at 4% annual rate, inserted before LivingExpenseFlow.
Interest compounds monthly throughout the simulation.

The scenario runs for 78 years (936 monthly turns):
- Person starts age 22, life expectancy 100 (78 years = 936 turns).
- Person has label Status="Working".
- Single checking account with ASSET label, initial balance $0.
- Monthly interest rate r = (1.04)^(1/12) - 1.
- Pipeline: AccountSolvencyGuardFlow, JobIncomeFlow, AccountInterestFlow,
  LivingExpenseFlow, PersonRetirementLabelFlow (triggers at age 61).

Expected outcome:
- result.success is True.
- Final checking balance is strictly positive (interest income on accumulated
  savings exceeds the symmetric drawdown).
- Final balance is within 5% of the analytically expected value.

Analytical formula (documented for spot-check):
  Working phase (turns 1–468):
    PMT_save = (100_000 - 50_000) / 12  (net monthly saving)
    r = (1.04) ** (1/12) - 1            (monthly interest rate)
    FV_work = PMT_save × ((1+r)^468 - 1) / r  (future value of saving annuity)

  Retirement phase (turns 469–936):
    PMT_draw = 50_000 / 12  (monthly withdrawal, income = 0)
    n_ret = 468             (retirement turns)
    PV_draw = PMT_draw × (1 - (1+r)^(-n_ret)) / r
              (present value at retirement of remaining withdrawals)
    FV_draw = PV_draw × (1+r)^n_ret
              (future value at end of simulation)

  Net final balance ≈ FV_work × (1+r)^468 - FV_draw
  (accumulated working savings grown over retirement years, minus drawdown FV)

  Note: the engine applies interest before the living expense each turn, so the
  order is: solvency check → income → interest → expense → retirement check.
  The analytical formula is therefore an approximation; a 5% tolerance is used.
"""

import math

from fitinera import (
    Age,
    Date,
    TurnDuration,
    Person,
    Account,
    SimulationScenario,
    SimulationEngine,
    EngineConfiguration,
)
from fitinera.flows import (
    AccountSolvencyGuardFlow,
    JobIncomeFlow,
    AccountInterestFlow,
    LivingExpenseFlow,
    PersonRetirementLabelFlow,
    PersonAgeIs,
    ComparisonOperator,
)


def _expected_final_balance() -> float:
    """Compute the analytically expected final balance for Scenario 2.

    The formula models two phases:

    Working phase (468 monthly turns, age 22–61):
      Net monthly PMT = 50_000 / 12
      FV_at_retirement = PMT × ((1+r)^n - 1) / r  (future value of annuity)
      (Interest is credited on the balance each turn before expenses are
      deducted, so this is approximately an end-of-period annuity.)

    Retirement phase (468 monthly turns, age 61–100):
      Monthly withdrawal = 50_000 / 12  (no income)
      Balance at end = FV_at_retirement × (1+r)^n_ret
                       - PMT_draw × ((1+r)^n_ret - 1) / r

    Returns:
        The analytically expected final balance (a strictly positive float).
    """
    annual_rate = 0.04
    r = (1 + annual_rate) ** (1 / 12) - 1
    n_work = 468
    n_ret = 468
    pmt_save = 50_000 / 12
    pmt_draw = 50_000 / 12

    # Future value of saving annuity at end of working phase.
    fv_at_retirement = pmt_save * ((1 + r) ** n_work - 1) / r

    # Grow accumulated savings through retirement.
    fv_grown = fv_at_retirement * (1 + r) ** n_ret

    # Future value of the drawdown annuity over retirement.
    fv_drawdown = pmt_draw * ((1 + r) ** n_ret - 1) / r

    return fv_grown - fv_drawdown


class TestScenarioSavingWithInterest:
    """Integration tests for Scenario 2: saving with monthly-compounding interest.

    Adding AccountInterestFlow to the Scenario 1 pipeline means interest
    accumulates on the checking balance throughout the working phase.  At
    retirement the accrued interest provides a cushion so the final balance
    is strictly positive.
    """

    def _build_scenario(self) -> SimulationScenario:
        """Return the SimulationScenario for Scenario 2.

        Returns:
            A SimulationScenario with one person (age 22, expectancy 100) and
            one ASSET-labeled checking account with zero initial balance.
        """
        return SimulationScenario(
            initial_persons=[
                Person(
                    id="person",
                    age=Age(years=22),
                    expectancy=Age(years=100),
                    labels={"Status": "Working"},
                )
            ],
            initial_accounts=[
                Account(
                    id="checking",
                    balance=0.0,
                    labels={"Type": "ASSET"},
                )
            ],
        )

    def _build_config(self) -> EngineConfiguration:
        """Return the EngineConfiguration for Scenario 2.

        AccountInterestFlow is inserted before LivingExpenseFlow so that
        interest is applied to the balance including that month's income
        before the expense is deducted.

        Returns:
            An EngineConfiguration with the Scenario 2 pipeline.
        """
        return EngineConfiguration(
            start_date=Date(year=2024, month=1),
            max_turns=TurnDuration.of(years=78),
            flows=[
                AccountSolvencyGuardFlow(),
                JobIncomeFlow(
                    person_id="person",
                    amount=100_000 / 12,
                    to_account="checking",
                ),
                AccountInterestFlow(
                    account_id="checking",
                    annual_rate=0.04,
                ),
                LivingExpenseFlow(
                    from_account="checking",
                    amount=50_000 / 12,
                ),
                PersonRetirementLabelFlow(
                    person_ids=["person"],
                    condition=PersonAgeIs(
                        "person",
                        ComparisonOperator.GE,
                        Age(61),
                    ),
                ),
            ],
        )

    def test_scenario_2_succeeds(self):
        """Running Scenario 2 produces result.success is True.

        The solvency guard never fires because compound interest ensures the
        balance stays non-negative throughout the simulation.
        """
        engine = SimulationEngine(self._build_config())
        result = engine.run(self._build_scenario())

        assert result.success is True

    def test_scenario_2_produces_936_turns(self):
        """Running Scenario 2 produces exactly 936 turns (78 years × 12 months).

        The simulation runs to max_turns because the person's life expectancy
        (age 100) is not reached within 936 turns from age 22.
        """
        engine = SimulationEngine(self._build_config())
        result = engine.run(self._build_scenario())

        assert len(result.turns) == 936

    def test_scenario_2_final_balance_is_strictly_positive(self):
        """Final checking account balance is strictly positive with interest.

        Interest on accumulated savings during the working phase creates a
        surplus that is never fully consumed during the retirement drawdown.
        """
        engine = SimulationEngine(self._build_config())
        result = engine.run(self._build_scenario())

        final_turn = result.turns[-1]
        checking = next(a for a in final_turn.accounts if a.id == "checking")

        assert checking.balance > 0.0

    def test_scenario_2_final_balance_within_5_percent_of_analytical(self):
        """Final balance is within 5% of the analytically expected value.

        The analytical formula (future value of annuity with monthly
        compounding, two-phase model) approximates the engine result.
        A 5% tolerance accommodates the discrete-time approximation inherent
        in the end-of-period annuity formula vs. the engine's intra-turn
        ordering (income → interest → expense).

        Analytical expected value formula:
          r = (1.04)^(1/12) - 1                   (monthly rate)
          n = 468                                  (working turns = retirement turns)
          PMT = 50_000 / 12                        (net saving / withdrawal)

          FV_work = PMT × ((1+r)^n - 1) / r       (accumulated at retirement)
          FV_final = FV_work × (1+r)^n             (grown through retirement)
                   - PMT × ((1+r)^n - 1) / r       (minus drawdown FV)
        """
        engine = SimulationEngine(self._build_config())
        result = engine.run(self._build_scenario())

        final_turn = result.turns[-1]
        checking = next(a for a in final_turn.accounts if a.id == "checking")
        actual = checking.balance

        expected = _expected_final_balance()
        tolerance = abs(expected) * 0.05

        assert math.isfinite(actual)
        assert abs(actual - expected) <= tolerance, (
            f"Final balance {actual:.2f} deviates more than 5% from "
            f"expected {expected:.2f} (tolerance ±{tolerance:.2f})"
        )

    def test_scenario_2_person_status_is_retired_after_age_61(self):
        """Person label Status transitions to 'Retired' once age 61 is reached.

        PersonRetirementLabelFlow fires when the person turns 61, so the final
        turn snapshot must show Status='Retired'.
        """
        engine = SimulationEngine(self._build_config())
        result = engine.run(self._build_scenario())

        final_turn = result.turns[-1]
        person = next(p for p in final_turn.persons if p.id == "person")

        assert person.get_label("Status") == "Retired"

    def test_scenario_2_error_message_is_none(self):
        """No error_message is set when the simulation completes successfully.

        A successful run (no logger.error called) must have error_message=None.
        """
        engine = SimulationEngine(self._build_config())
        result = engine.run(self._build_scenario())

        assert result.error_message is None
