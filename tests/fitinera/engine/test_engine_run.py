"""Tests for SimulationEngine.run() and engine internals.

Covers _SimulationStateViewImpl, _SimulationStateUpdaterImpl, _SimulationLoggerImpl,
and the full engine dispatch loop per task-10 acceptance criteria.
"""

import logging
from typing import List


from fitinera.engine import EngineConfiguration, SimulationEngine
from fitinera.flows import AccountSolvencyGuardFlow
from fitinera.models import (
    Account,
    AccountState,
    Age,
    Date,
    Expense,
    Income,
    Person,
    SimulationScenario,
    Transfer,
    TurnDuration,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_config(
    *,
    start_date: Date = Date(2026, 1),
    max_turns: TurnDuration = TurnDuration(1),
    flows=None,
    metrics=None,
) -> EngineConfiguration:
    """Return a minimal EngineConfiguration."""
    kwargs = dict(start_date=start_date, max_turns=max_turns)
    if flows is not None:
        kwargs["flows"] = flows
    if metrics is not None:
        kwargs["metrics"] = metrics
    return EngineConfiguration(**kwargs)


def _make_person(
    pid: str = "p1",
    age_years: int = 30,
    expectancy_years: int = 90,
    labels=None,
) -> Person:
    return Person(
        id=pid,
        age=Age(age_years),
        expectancy=Age(expectancy_years),
        labels=labels or {},
    )


def _make_account(
    aid: str = "checking", balance: float = 1000.0, labels=None
) -> Account:
    return Account(id=aid, balance=balance, labels=labels or {})


# ---------------------------------------------------------------------------
# TestEngineRunBasic
# ---------------------------------------------------------------------------


class TestEngineRunBasic:
    """Basic engine.run() smoke tests.

    Verify the engine produces a valid SimulationResult for the simplest
    possible scenarios.
    """

    def test_run_returns_simulation_result_with_success_true(self):
        """A single-turn scenario with one person returns success=True."""
        config = _make_config(max_turns=TurnDuration(1))
        engine = SimulationEngine(config)
        scenario = SimulationScenario(
            initial_persons=[_make_person()],
            initial_accounts=[_make_account()],
        )

        result = engine.run(scenario)

        assert result.success is True
        assert result.error_message is None

    def test_run_produces_at_least_one_turn(self):
        """Engine returns at least one turn for max_turns=TurnDuration(1)."""
        config = _make_config(max_turns=TurnDuration(1))
        engine = SimulationEngine(config)
        scenario = SimulationScenario(
            initial_persons=[_make_person()],
            initial_accounts=[_make_account()],
        )

        result = engine.run(scenario)

        assert len(result.turns) >= 1

    def test_run_with_empty_scenario_returns_success(self):
        """An empty scenario (no persons, no accounts) runs without error."""
        config = _make_config(max_turns=TurnDuration(1))
        engine = SimulationEngine(config)
        scenario = SimulationScenario()

        result = engine.run(scenario)

        assert result.success is True

    def test_run_produces_exactly_max_turns_turns_by_month_count(self):
        """Engine produces a turn per month for TurnDuration(0, months=3)."""
        config = _make_config(max_turns=TurnDuration(0, months=3))
        engine = SimulationEngine(config)
        scenario = SimulationScenario(initial_persons=[_make_person()])

        result = engine.run(scenario)

        # 3 months → 3 turns
        assert len(result.turns) == 3

    def test_run_produces_correct_turn_count_for_years(self):
        """Engine produces one turn per calendar month for TurnDuration(1) = 12 turns."""
        config = _make_config(max_turns=TurnDuration(1))
        engine = SimulationEngine(config)
        scenario = SimulationScenario(initial_persons=[_make_person()])

        result = engine.run(scenario)

        assert len(result.turns) == 12


# ---------------------------------------------------------------------------
# TestEngineRunTurnSnapshot
# ---------------------------------------------------------------------------


class TestEngineRunTurnSnapshot:
    """Tests verifying the contents of per-turn snapshots.

    Each Turn must contain frozen Account/Person snapshots reflecting
    post-flow state, the turn date, and the transaction list.
    """

    def test_turn_snapshot_contains_accounts(self):
        """Each Turn snapshot includes frozen Account objects."""
        config = _make_config(max_turns=TurnDuration(0, months=1))
        engine = SimulationEngine(config)
        scenario = SimulationScenario(initial_accounts=[_make_account()])

        result = engine.run(scenario)

        assert len(result.turns) == 1
        turn = result.turns[0]
        assert len(turn.accounts) == 1
        assert turn.accounts[0].id == "checking"

    def test_turn_snapshot_contains_persons(self):
        """Each Turn snapshot includes frozen Person objects."""
        config = _make_config(max_turns=TurnDuration(0, months=1))
        engine = SimulationEngine(config)
        scenario = SimulationScenario(initial_persons=[_make_person("p1")])

        result = engine.run(scenario)

        assert len(result.turns) == 1
        turn = result.turns[0]
        assert len(turn.persons) == 1
        assert turn.persons[0].id == "p1"

    def test_turn_snapshot_account_balance_reflects_construction_balance(self):
        """Turn snapshot account balance matches the construction balance when no flows run."""
        config = _make_config(max_turns=TurnDuration(0, months=1))
        engine = SimulationEngine(config)
        scenario = SimulationScenario(initial_accounts=[_make_account(balance=5000.0)])

        result = engine.run(scenario)

        turn = result.turns[0]
        assert turn.accounts[0].balance == 5000.0

    def test_turn_date_advances_by_one_month_per_turn(self):
        """Each Turn.date is one calendar month ahead of the previous."""
        config = _make_config(
            start_date=Date(2026, 1), max_turns=TurnDuration(0, months=3)
        )
        engine = SimulationEngine(config)
        scenario = SimulationScenario()

        result = engine.run(scenario)

        assert result.turns[0].date == Date(2026, 2)
        assert result.turns[1].date == Date(2026, 3)
        assert result.turns[2].date == Date(2026, 4)

    def test_turn_date_rolls_year_on_december_to_january(self):
        """Date increments from December to January of the next year correctly."""
        config = _make_config(
            start_date=Date(2026, 12), max_turns=TurnDuration(0, months=2)
        )
        engine = SimulationEngine(config)
        scenario = SimulationScenario()

        result = engine.run(scenario)

        assert result.turns[0].date == Date(2027, 1)
        assert result.turns[1].date == Date(2027, 2)

    def test_person_age_increments_by_one_month_per_turn(self):
        """Person.age advances by one month each turn in the snapshot."""
        config = _make_config(max_turns=TurnDuration(0, months=3))
        engine = SimulationEngine(config)
        scenario = SimulationScenario(
            initial_persons=[_make_person(age_years=30)]  # Age(30) = years=30, months=0
        )

        result = engine.run(scenario)

        assert result.turns[0].persons[0].age == Age(30, months=1)
        assert result.turns[1].persons[0].age == Age(30, months=2)
        assert result.turns[2].persons[0].age == Age(30, months=3)

    def test_person_age_rolls_months_to_years(self):
        """Person age rolls months=12 → next year, months=0."""
        # Create a person starting at age(30, months=11) so next month → age(31, 0)
        config = _make_config(max_turns=TurnDuration(0, months=1))
        engine = SimulationEngine(config)
        person = Person(id="p1", age=Age(30, 11), expectancy=Age(90))
        scenario = SimulationScenario(initial_persons=[person])

        result = engine.run(scenario)

        assert result.turns[0].persons[0].age == Age(31, 0)


# ---------------------------------------------------------------------------
# TestEngineRunTransactions
# ---------------------------------------------------------------------------


class TestEngineRunTransactions:
    """Tests verifying transaction application and buffering.

    Confirms that flows' emitted transactions mutate account balances
    and appear in the turn transaction list.
    """

    def test_income_transaction_increases_account_balance(self):
        """Income emitted by a flow increases the target account balance."""
        from fitinera.models import Income

        class _IncomeFlow:
            def executeFlow(self, view, updater, logger):
                updater.emit_transaction(Income(amount=500.0, to_account="checking"))

        config = _make_config(
            max_turns=TurnDuration(0, months=1), flows=[_IncomeFlow()]
        )
        engine = SimulationEngine(config)
        scenario = SimulationScenario(initial_accounts=[_make_account(balance=1000.0)])

        result = engine.run(scenario)

        assert result.turns[0].accounts[0].balance == 1500.0

    def test_expense_transaction_decreases_account_balance(self):
        """Expense emitted by a flow decreases the source account balance."""

        class _ExpenseFlow:
            def executeFlow(self, view, updater, logger):
                updater.emit_transaction(Expense(amount=200.0, from_account="checking"))

        config = _make_config(
            max_turns=TurnDuration(0, months=1), flows=[_ExpenseFlow()]
        )
        engine = SimulationEngine(config)
        scenario = SimulationScenario(initial_accounts=[_make_account(balance=1000.0)])

        result = engine.run(scenario)

        assert result.turns[0].accounts[0].balance == 800.0

    def test_transfer_transaction_moves_funds_between_accounts(self):
        """Transfer emitted by a flow moves funds from one account to another."""

        class _TransferFlow:
            def executeFlow(self, view, updater, logger):
                updater.emit_transaction(
                    Transfer(
                        amount=300.0, from_account="checking", to_account="savings"
                    )
                )

        config = _make_config(
            max_turns=TurnDuration(0, months=1), flows=[_TransferFlow()]
        )
        engine = SimulationEngine(config)
        scenario = SimulationScenario(
            initial_accounts=[
                _make_account("checking", 1000.0),
                _make_account("savings", 500.0),
            ]
        )

        result = engine.run(scenario)

        accounts = {a.id: a for a in result.turns[0].accounts}
        assert accounts["checking"].balance == 700.0
        assert accounts["savings"].balance == 800.0

    def test_transaction_buffer_cleared_between_turns(self):
        """Each Turn.transactions contains only transactions emitted in that turn."""
        from fitinera.models import Income

        class _IncomeFlow:
            def executeFlow(self, view, updater, logger):
                updater.emit_transaction(Income(amount=100.0, to_account="checking"))

        config = _make_config(
            max_turns=TurnDuration(0, months=2), flows=[_IncomeFlow()]
        )
        engine = SimulationEngine(config)
        scenario = SimulationScenario(initial_accounts=[_make_account(balance=0.0)])

        result = engine.run(scenario)

        # Each turn should have exactly 1 transaction (not cumulative)
        assert len(result.turns[0].transactions) == 1
        assert len(result.turns[1].transactions) == 1

    def test_subsequent_flows_see_updated_balance(self):
        """A Flow later in the pipeline sees balance changes from earlier flows (ADR-0005)."""
        from fitinera.models import Income

        seen_balances: List[float] = []

        class _IncomeFlow:
            def executeFlow(self, view, updater, logger):
                updater.emit_transaction(Income(amount=500.0, to_account="checking"))

        class _ObserverFlow:
            def executeFlow(self, view, updater, logger):
                accounts = view.get_accounts()
                for a in accounts:
                    if a.id == "checking":
                        seen_balances.append(a.balance)

        config = _make_config(
            max_turns=TurnDuration(0, months=1),
            flows=[_IncomeFlow(), _ObserverFlow()],
        )
        engine = SimulationEngine(config)
        scenario = SimulationScenario(initial_accounts=[_make_account(balance=1000.0)])

        engine.run(scenario)

        assert seen_balances == [1500.0]


# ---------------------------------------------------------------------------
# TestEngineRunHaltConditions
# ---------------------------------------------------------------------------


class TestEngineRunHaltConditions:
    """Tests verifying halt conditions (FR-023).

    Covers logger-error halt, all-persons-deceased halt, and max_turns halt.
    """

    def test_logger_error_halts_engine_with_success_false(self):
        """Engine halts immediately and returns success=False when a flow logs error."""

        class _ErrorFlow:
            def executeFlow(self, view, updater, logger):
                logger.error("Insolvency detected")

        config = _make_config(max_turns=TurnDuration(1), flows=[_ErrorFlow()])
        engine = SimulationEngine(config)
        scenario = SimulationScenario(initial_persons=[_make_person()])

        result = engine.run(scenario)

        assert result.success is False
        assert result.error_message is not None
        assert "Insolvency" in result.error_message

    def test_logger_error_halts_before_snapshot(self):
        """Engine does not add a turn snapshot for the turn where an error occurred."""

        class _ErrorFlow:
            def executeFlow(self, view, updater, logger):
                logger.error("Fatal error")

        config = _make_config(
            start_date=Date(2026, 1),
            max_turns=TurnDuration(1),
            flows=[_ErrorFlow()],
        )
        engine = SimulationEngine(config)
        scenario = SimulationScenario(initial_persons=[_make_person()])

        result = engine.run(scenario)

        # No turns should be snapshotted because the error occurred before snapshot step
        assert len(result.turns) == 0

    def test_all_persons_deceased_halts_with_success_true(self):
        """Engine halts with success=True when all persons are no longer living."""
        # Person at age=89yr 11mo, expectancy=90yr: after 1 turn age=90yr 0mo → not living
        person = Person(id="p1", age=Age(89, 11), expectancy=Age(90, 0))
        config = _make_config(max_turns=TurnDuration(years=5))
        engine = SimulationEngine(config)
        scenario = SimulationScenario(initial_persons=[person])

        result = engine.run(scenario)

        assert result.success is True
        # Should halt before max_turns (5 years = 60 turns) after 1 turn
        assert len(result.turns) < 60

    def test_max_turns_reached_halts_with_success_true(self):
        """Engine halts with success=True when max_turns is exhausted."""
        # Person with long life expectancy — should not halt early
        config = _make_config(max_turns=TurnDuration(0, months=5))
        engine = SimulationEngine(config)
        scenario = SimulationScenario(
            initial_persons=[_make_person(expectancy_years=200)]
        )

        result = engine.run(scenario)

        assert result.success is True
        assert len(result.turns) == 5

    def test_solvency_guard_triggers_failure_on_negative_balance(self):
        """AccountSolvencyGuardFlow causes result.success=False for negative-balance account."""
        config = _make_config(
            max_turns=TurnDuration(1),
            flows=[AccountSolvencyGuardFlow()],
        )
        engine = SimulationEngine(config)
        scenario = SimulationScenario(
            initial_accounts=[_make_account(balance=-500.0, labels={"Type": "ASSET"})]
        )

        result = engine.run(scenario)

        assert result.success is False


# ---------------------------------------------------------------------------
# TestEngineRunViewImpl
# ---------------------------------------------------------------------------


class TestEngineRunViewImpl:
    """Tests verifying _SimulationStateViewImpl behaviour via a probe flow."""

    def test_get_accounts_returns_account_states(self):
        """view.get_accounts() returns AccountState objects with correct ids."""
        seen = []

        class _ProbeFlow:
            def executeFlow(self, view, updater, logger):
                seen.extend(view.get_accounts())

        config = _make_config(max_turns=TurnDuration(0, months=1), flows=[_ProbeFlow()])
        engine = SimulationEngine(config)
        scenario = SimulationScenario(
            initial_accounts=[_make_account("checking"), _make_account("savings")]
        )

        engine.run(scenario)

        ids = {a.id for a in seen}
        assert "checking" in ids
        assert "savings" in ids
        # Must be AccountState (mutable), not Account (frozen)
        assert all(isinstance(a, AccountState) for a in seen)

    def test_get_person_returns_person_for_known_id(self):
        """view.get_person(id) returns a Person with matching id."""
        seen = []

        class _ProbeFlow:
            def executeFlow(self, view, updater, logger):
                p = view.get_person("p1")
                if p is not None:
                    seen.append(p)

        config = _make_config(max_turns=TurnDuration(0, months=1), flows=[_ProbeFlow()])
        engine = SimulationEngine(config)
        scenario = SimulationScenario(initial_persons=[_make_person("p1")])

        engine.run(scenario)

        assert len(seen) == 1
        assert seen[0].id == "p1"

    def test_get_person_returns_none_for_unknown_id(self):
        """view.get_person(unknown) returns None."""
        seen = []

        class _ProbeFlow:
            def executeFlow(self, view, updater, logger):
                seen.append(view.get_person("unknown"))

        config = _make_config(max_turns=TurnDuration(0, months=1), flows=[_ProbeFlow()])
        engine = SimulationEngine(config)
        scenario = SimulationScenario()

        engine.run(scenario)

        assert seen == [None]

    def test_get_start_date_returns_config_start_date(self):
        """view.get_start_date() returns the EngineConfiguration.start_date."""
        seen = []

        class _ProbeFlow:
            def executeFlow(self, view, updater, logger):
                seen.append(view.get_start_date())

        config = _make_config(
            start_date=Date(2030, 6),
            max_turns=TurnDuration(0, months=1),
            flows=[_ProbeFlow()],
        )
        engine = SimulationEngine(config)
        scenario = SimulationScenario()

        engine.run(scenario)

        assert seen[0] == Date(2030, 6)

    def test_get_current_date_returns_current_turn_date(self):
        """view.get_current_date() returns the current (incremented) date."""
        seen = []

        class _ProbeFlow:
            def executeFlow(self, view, updater, logger):
                seen.append(view.get_current_date())

        config = _make_config(
            start_date=Date(2026, 1),
            max_turns=TurnDuration(0, months=2),
            flows=[_ProbeFlow()],
        )
        engine = SimulationEngine(config)
        scenario = SimulationScenario()

        engine.run(scenario)

        assert seen[0] == Date(2026, 2)
        assert seen[1] == Date(2026, 3)

    def test_get_elapsed_duration_returns_turns_completed(self):
        """view.get_elapsed_duration().months equals number of turns completed so far."""
        seen = []

        class _ProbeFlow:
            def executeFlow(self, view, updater, logger):
                seen.append(view.get_elapsed_duration().months)

        config = _make_config(max_turns=TurnDuration(0, months=3), flows=[_ProbeFlow()])
        engine = SimulationEngine(config)
        scenario = SimulationScenario()

        engine.run(scenario)

        assert seen == [0, 1, 2]

    def test_get_current_turn_transactions_returns_buffered_transactions(self):
        """view.get_current_turn_transactions() returns transactions emitted so far this turn."""
        seen = []

        class _EmitFlow:
            def executeFlow(self, view, updater, logger):
                updater.emit_transaction(Income(amount=100.0, to_account="checking"))

        class _ProbeFlow:
            def executeFlow(self, view, updater, logger):
                seen.append(list(view.get_current_turn_transactions()))

        config = _make_config(
            max_turns=TurnDuration(0, months=1),
            flows=[_EmitFlow(), _ProbeFlow()],
        )
        engine = SimulationEngine(config)
        scenario = SimulationScenario(initial_accounts=[_make_account()])

        engine.run(scenario)

        assert len(seen[0]) == 1
        assert isinstance(seen[0][0], Income)

    def test_get_metric_evaluates_metric_generator(self):
        """view.get_metric(name) calls the corresponding MetricGenerator.evaluate()."""
        seen = []

        class _TotalBalanceMetric:
            def evaluate(self, view, logger):
                return sum(a.balance for a in view.get_accounts())

        class _ProbeFlow:
            def executeFlow(self, view, updater, logger):
                seen.append(view.get_metric("total"))

        config = _make_config(
            max_turns=TurnDuration(0, months=1),
            flows=[_ProbeFlow()],
            metrics={"total": _TotalBalanceMetric()},
        )
        engine = SimulationEngine(config)
        scenario = SimulationScenario(initial_accounts=[_make_account(balance=2500.0)])

        engine.run(scenario)

        assert seen[0] == 2500.0


# ---------------------------------------------------------------------------
# TestEngineRunUpdaterImpl
# ---------------------------------------------------------------------------


class TestEngineRunUpdaterImpl:
    """Tests verifying _SimulationStateUpdaterImpl behaviour."""

    def test_update_person_label_mutates_person_labels(self):
        """updater.update_person_label() changes the person's label visible via get_person()."""

        class _LabelFlow:
            def executeFlow(self, view, updater, logger):
                updater.update_person_label("p1", "Status", "Retired")

        class _ProbeFlow:
            def __init__(self):
                self.label_after = None

            def executeFlow(self, view, updater, logger):
                p = view.get_person("p1")
                if p:
                    self.label_after = p.get_label("Status")

        probe = _ProbeFlow()
        config = _make_config(
            max_turns=TurnDuration(0, months=1),
            flows=[_LabelFlow(), probe],
        )
        engine = SimulationEngine(config)
        scenario = SimulationScenario(initial_persons=[_make_person("p1")])

        engine.run(scenario)

        assert probe.label_after == "Retired"

    def test_person_label_update_persists_across_turns(self):
        """A label set in turn N is visible in turn N+1."""
        label_values = []

        class _SetLabelTurn1:
            def __init__(self):
                self.called = 0

            def executeFlow(self, view, updater, logger):
                self.called += 1
                if self.called == 1:
                    updater.update_person_label("p1", "Status", "Retired")

        class _ProbeFlow:
            def executeFlow(self, view, updater, logger):
                p = view.get_person("p1")
                if p:
                    label_values.append(p.get_label("Status"))

        setter = _SetLabelTurn1()
        config = _make_config(
            max_turns=TurnDuration(0, months=2),
            flows=[setter, _ProbeFlow()],
        )
        engine = SimulationEngine(config)
        scenario = SimulationScenario(initial_persons=[_make_person("p1")])

        engine.run(scenario)

        # Turn 1: label set to "Retired" before probe
        assert label_values[0] == "Retired"
        # Turn 2: label persists
        assert label_values[1] == "Retired"


# ---------------------------------------------------------------------------
# TestEngineRunLoggerImpl
# ---------------------------------------------------------------------------


class TestEngineRunLoggerImpl:
    """Tests verifying _SimulationLoggerImpl behaviour."""

    def test_logger_debug_does_not_halt_engine(self):
        """Calling logger.debug() does not cause engine halt or failure."""

        class _DebugFlow:
            def executeFlow(self, view, updater, logger):
                logger.debug("debug message")

        config = _make_config(max_turns=TurnDuration(0, months=1), flows=[_DebugFlow()])
        engine = SimulationEngine(config)
        scenario = SimulationScenario()

        result = engine.run(scenario)

        assert result.success is True

    def test_logger_info_does_not_halt_engine(self):
        """Calling logger.info() does not cause engine halt or failure."""

        class _InfoFlow:
            def executeFlow(self, view, updater, logger):
                logger.info("info message")

        config = _make_config(max_turns=TurnDuration(0, months=1), flows=[_InfoFlow()])
        engine = SimulationEngine(config)
        scenario = SimulationScenario()

        result = engine.run(scenario)

        assert result.success is True

    def test_logger_warning_does_not_halt_engine(self):
        """Calling logger.warning() does not cause engine halt or failure."""

        class _WarnFlow:
            def executeFlow(self, view, updater, logger):
                logger.warning("warning message")

        config = _make_config(max_turns=TurnDuration(0, months=1), flows=[_WarnFlow()])
        engine = SimulationEngine(config)
        scenario = SimulationScenario()

        result = engine.run(scenario)

        assert result.success is True

    def test_logger_error_sets_failure(self):
        """Calling logger.error() causes engine to return success=False."""

        class _ErrorFlow:
            def executeFlow(self, view, updater, logger):
                logger.error("critical failure")

        config = _make_config(max_turns=TurnDuration(0, months=1), flows=[_ErrorFlow()])
        engine = SimulationEngine(config)
        scenario = SimulationScenario()

        result = engine.run(scenario)

        assert result.success is False

    def test_logger_error_message_stored_in_result(self):
        """The error message passed to logger.error() appears in result.error_message."""

        class _ErrorFlow:
            def executeFlow(self, view, updater, logger):
                logger.error("account insolvent at turn 1")

        config = _make_config(max_turns=TurnDuration(0, months=1), flows=[_ErrorFlow()])
        engine = SimulationEngine(config)
        scenario = SimulationScenario()

        result = engine.run(scenario)

        assert result.error_message == "account insolvent at turn 1"

    def test_logger_writes_to_fitinera_engine_logger(self, caplog):
        """Logger methods write to the 'fitinera.engine' Python logger."""

        class _LogAllLevels:
            def executeFlow(self, view, updater, logger):
                logger.debug("dbg")
                logger.info("inf")
                logger.warning("wrn")

        config = _make_config(
            max_turns=TurnDuration(0, months=1), flows=[_LogAllLevels()]
        )
        engine = SimulationEngine(config)
        scenario = SimulationScenario()

        with caplog.at_level(logging.DEBUG, logger="fitinera.engine"):
            engine.run(scenario)

        messages = [r.message for r in caplog.records]
        assert "dbg" in messages
        assert "inf" in messages
        assert "wrn" in messages
