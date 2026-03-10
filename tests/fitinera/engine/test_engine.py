import pytest
from fitinera.engine import SimulationEngine, EngineConfiguration
from fitinera.engine.exceptions import SolvencyViolationError
from fitinera.flows import AccountSolvencyGuardFlow, LivingExpenseFlow
from fitinera.models import Account, SimulationScenario, Date, TurnDuration
from fitinera import SimulationResult


def test_simulation_engine_initialization_takes_configuration():
    config = EngineConfiguration(Date(2026, 1), TurnDuration.of(years=10))
    engine = SimulationEngine(config)
    assert engine.configuration is config


class TestSimulationResultShape:
    """Tests verifying SimulationResult dataclass shape and field types.

    These tests confirm that SimulationResult is a frozen dataclass with only
    the turns field.
    """

    def test_simulation_result_can_be_constructed_with_turns(self):
        """SimulationResult accepts a turns list at construction."""
        result = SimulationResult(turns=[])
        assert result.turns == []

    def test_simulation_result_turns_defaults_to_empty_list(self):
        """SimulationResult.turns defaults to an empty list when not provided."""
        result = SimulationResult()
        assert result.turns == []

    def test_simulation_result_is_frozen(self):
        """SimulationResult is immutable; field assignment raises FrozenInstanceError."""
        result = SimulationResult(turns=[])
        with pytest.raises(Exception):
            result.turns = []  # type: ignore[misc]

    def test_simulation_result_turns_field_accepts_list(self):
        """SimulationResult.turns is a list, indexable and iterable."""
        result = SimulationResult(turns=[])
        assert isinstance(result.turns, list)
        assert len(result.turns) == 0

    def test_simulation_result_has_no_success_field(self):
        """SimulationResult no longer has a success field."""
        result = SimulationResult(turns=[])
        assert not hasattr(result, "success")

    def test_simulation_result_has_no_error_message_field(self):
        """SimulationResult no longer has an error_message field."""
        result = SimulationResult(turns=[])
        assert not hasattr(result, "error_message")

    def test_simulation_result_has_no_log_messages_field(self):
        """SimulationResult no longer has a log_messages field."""
        result = SimulationResult(turns=[])
        assert not hasattr(result, "log_messages")


def test_engine_raises_solvency_violation_on_logger_error():
    """Engine propagates SolvencyViolationError raised by a flow."""
    from fitinera.models import Age, Person

    config = EngineConfiguration(
        start_date=Date(2026, 1),
        max_turns=TurnDuration.of(years=1),
        flows=[AccountSolvencyGuardFlow()],
    )
    engine = SimulationEngine(config)
    scenario = SimulationScenario(
        initial_persons=[Person(id="p1", age=Age(30), expectancy=Age(90))],
        initial_accounts=[
            Account(id="checking", balance=-500.0, labels={"Type": "ASSET"})
        ],
    )

    with pytest.raises(SolvencyViolationError):
        engine.run(scenario)


class TestEngineIntegration:
    """Integration-level tests for SimulationEngine.run().

    These tests define the expected engine behaviour for end-to-end scenarios.
    """

    def test_minimal_single_turn_scenario_returns_turns(self):
        """A scenario with one person and one account and no flows produces at least one turn.

        The engine must produce a SimulationResult where result.turns has at least
        one entry when no flows raise an exception.
        """
        from fitinera.models import Age, Person

        config = EngineConfiguration(
            start_date=Date(2026, 1), max_turns=TurnDuration.of(years=1)
        )
        engine = SimulationEngine(config)
        scenario = SimulationScenario(
            initial_persons=[Person(id="p1", age=Age(30), expectancy=Age(90))],
            initial_accounts=[Account(id="checking", balance=1000.0)],
        )

        result = engine.run(scenario)

        assert len(result.turns) >= 1

    def test_solvency_guard_flow_raises_on_negative_balance(self):
        """AccountSolvencyGuardFlow raises SolvencyViolationError when an ASSET account is negative.

        When AccountSolvencyGuardFlow is included in the pipeline and the initial
        balance of an ASSET-labeled account is negative, the engine raises
        SolvencyViolationError.
        """
        config = EngineConfiguration(
            start_date=Date(2026, 1),
            max_turns=TurnDuration.of(years=1),
            flows=[AccountSolvencyGuardFlow()],
        )
        engine = SimulationEngine(config)
        scenario = SimulationScenario(
            initial_accounts=[
                Account(id="checking", balance=-500.0, labels={"Type": "ASSET"})
            ],
        )

        with pytest.raises(SolvencyViolationError):
            engine.run(scenario)


def test_engine_raises_when_living_expense_drains_account_negative():
    """Engine raises SolvencyViolationError when LivingExpenseFlow drains account below zero."""
    config = EngineConfiguration(
        start_date=Date(2026, 1),
        max_turns=TurnDuration.of(years=1),
        flows=[
            LivingExpenseFlow(from_account="checking", amount=200.0),
            AccountSolvencyGuardFlow(),
        ],
    )
    engine = SimulationEngine(config)
    scenario = SimulationScenario(
        initial_accounts=[
            Account(id="checking", balance=100.0, labels={"Type": "ASSET"})
        ],
    )

    with pytest.raises(SolvencyViolationError):
        engine.run(scenario)


def test_engine_solvency_error_message_contains_account_id():
    """Solvency violation error message identifies the insolvent account by id."""
    config = EngineConfiguration(
        start_date=Date(2026, 1),
        max_turns=TurnDuration.of(years=1),
        flows=[
            LivingExpenseFlow(from_account="checking", amount=200.0),
            AccountSolvencyGuardFlow(),
        ],
    )
    engine = SimulationEngine(config)
    scenario = SimulationScenario(
        initial_accounts=[
            Account(id="checking", balance=100.0, labels={"Type": "ASSET"})
        ],
    )

    with pytest.raises(SolvencyViolationError, match="checking"):
        engine.run(scenario)


def test_engine_logger_error_does_not_halt_simulation():
    """Calling logger.error() is now purely observational and does not halt the simulation."""

    class _ErrorLogFlow:
        def executeFlow(self, view, updater, logger):
            logger.error("non-fatal observation")

    config = EngineConfiguration(
        start_date=Date(2026, 1),
        max_turns=TurnDuration.of(months=1),
        flows=[_ErrorLogFlow()],
    )
    engine = SimulationEngine(config)
    scenario = SimulationScenario()

    result = engine.run(scenario)

    assert len(result.turns) == 1
