"""Integration test: Scenario 1 — Simple saving without interest.

This scenario validates the basic engine loop with a single working person who
saves half of their income each month and retires at age 61.  With no interest,
the account balance is expected to return to $0.00 at the end of the simulation.

The scenario runs for 78 years (936 monthly turns):
- Person starts age 22, life expectancy 100 (78 years = 936 turns).
- Person has label Status="Working".
- Single checking account with ASSET label, initial balance $0, no interest.
- Pipeline: AccountSolvencyGuardFlow, JobIncomeFlow, LivingExpenseFlow,
  PersonRetirementLabelFlow (triggers at age 61).

Expected outcome (FR-024):
- result.success is True.
- Final checking account balance is within $0.01 of $0.00.

Math:
  Working phase (turns 1-468, age 22 → just before 61):
    Net monthly savings = (100_000 - 50_000) / 12
    Balance at retirement = 468 × (50_000 / 12) ≈ $1_950_000
  Retirement phase (turns 469-936, age 61 → ~100):
    Monthly expense = 50_000 / 12  (income is zero — Status="Retired")
    Drawdown over 468 turns = 468 × (50_000 / 12) ≈ $1_950_000
  Final balance = $1_950_000 - $1_950_000 = $0.00
"""

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
    LivingExpenseFlow,
    PersonRetirementLabelFlow,
    PersonAgeIs,
    ComparisonOperator,
)


class TestScenarioSimpleSaving:
    """Integration tests for Scenario 1: simple saving with no interest.

    The scenario exercises a complete 936-turn simulation where a single person
    saves half their income during a working career and then draws down savings
    in retirement.  The absence of interest means savings and drawdown are
    symmetric, producing a final balance of approximately $0.
    """

    def _build_scenario(self) -> SimulationScenario:
        """Return the SimulationScenario for Scenario 1.

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
        """Return the EngineConfiguration for Scenario 1.

        The pipeline runs for 78 years (936 monthly turns).  Retirement
        triggers when the person reaches age 61 (PersonAgeIs GE Age(61)).

        Returns:
            An EngineConfiguration with the Scenario 1 pipeline.
        """
        return EngineConfiguration(
            start_date=Date(year=2024, month=1),
            max_turns=TurnDuration(years=78),
            flows=[
                AccountSolvencyGuardFlow(),
                JobIncomeFlow(
                    person_id="person",
                    amount=100_000 / 12,
                    to_account="checking",
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

    def test_scenario_1_succeeds(self):
        """Running Scenario 1 produces result.success is True.

        The solvency guard never fires because the balance is never negative
        during the working phase, so the simulation reaches max_turns
        successfully.
        """
        engine = SimulationEngine(self._build_config())
        result = engine.run(self._build_scenario())

        assert result.success is True

    def test_scenario_1_produces_936_turns(self):
        """Running Scenario 1 produces exactly 936 turns (78 years × 12 months).

        The simulation runs to max_turns because the person's life expectancy
        (age 100) is not reached within 936 turns from age 22.
        """
        engine = SimulationEngine(self._build_config())
        result = engine.run(self._build_scenario())

        assert len(result.turns) == 936

    def test_scenario_1_final_balance_is_zero(self):
        """Final checking account balance is within $0.01 of $0.00 (FR-024).

        With symmetric saving and drawdown and no interest, the working-phase
        accumulation exactly offsets the retirement-phase drawdown.
        """
        engine = SimulationEngine(self._build_config())
        result = engine.run(self._build_scenario())

        final_turn = result.turns[-1]
        checking = next(a for a in final_turn.accounts if a.id == "checking")

        assert abs(checking.balance - 0.0) < 0.01

    def test_scenario_1_person_status_is_retired_after_age_61(self):
        """Person label Status transitions to 'Retired' once age 61 is reached.

        PersonRetirementLabelFlow fires when the person turns 61, so the final
        turn snapshot must show Status='Retired'.
        """
        engine = SimulationEngine(self._build_config())
        result = engine.run(self._build_scenario())

        final_turn = result.turns[-1]
        person = next(p for p in final_turn.persons if p.id == "person")

        assert person.get_label("Status") == "Retired"

    def test_scenario_1_error_message_is_none(self):
        """No error_message is set when the simulation completes successfully.

        A successful run (no logger.error called) must have error_message=None.
        """
        engine = SimulationEngine(self._build_config())
        result = engine.run(self._build_scenario())

        assert result.error_message is None
