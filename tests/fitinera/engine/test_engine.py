import pytest
from fitinera.engine import SimulationEngine, EngineConfiguration
from fitinera.flows import AccountSolvencyGuardFlow, LivingExpenseFlow
from fitinera.models import Account, SimulationScenario, Date, TurnDuration
from fitinera import SimulationResult


def test_simulation_engine_initialization_takes_configuration():
    config = EngineConfiguration(Date(2026, 1), TurnDuration(10, 0))
    engine = SimulationEngine(config)
    assert engine.configuration is config


class TestSimulationResultShape:
    """Tests verifying SimulationResult dataclass shape and field types.

    These tests confirm that SimulationResult is a frozen dataclass with the
    expected fields: turns (list), success (bool), and optional error_message.
    """

    def test_simulation_result_can_be_constructed_with_required_fields(self):
        """SimulationResult accepts turns list and success bool at construction."""
        result = SimulationResult(turns=[], success=True)
        assert result.turns == []
        assert result.success is True

    def test_simulation_result_error_message_defaults_to_none(self):
        """SimulationResult.error_message is None when not provided."""
        result = SimulationResult(turns=[], success=True)
        assert result.error_message is None

    def test_simulation_result_accepts_error_message(self):
        """SimulationResult stores an explicit error_message when provided."""
        result = SimulationResult(turns=[], success=False, error_message="Insolvent")
        assert result.error_message == "Insolvent"
        assert result.success is False

    def test_simulation_result_is_frozen(self):
        """SimulationResult is immutable; field assignment raises FrozenInstanceError."""
        result = SimulationResult(turns=[], success=True)
        with pytest.raises(Exception):
            result.success = False  # type: ignore[misc]

    def test_simulation_result_turns_field_accepts_list(self):
        """SimulationResult.turns is a list, indexable and iterable."""
        result = SimulationResult(turns=[], success=True)
        assert isinstance(result.turns, list)
        assert len(result.turns) == 0


def test_engine_halts_on_logger_error():
    """Engine returns success=False when a flow emits a logger error."""
    from fitinera.models import Age, Person

    class _ErrorFlow:
        def executeFlow(self, view, updater, logger):
            logger.error("fatal error")

    config = EngineConfiguration(
        start_date=Date(2026, 1),
        max_turns=TurnDuration(1, 0),
        flows=[_ErrorFlow()],
    )
    engine = SimulationEngine(config)
    scenario = SimulationScenario(
        initial_persons=[Person(id="p1", age=Age(30), expectancy=Age(90))]
    )

    result = engine.run(scenario)

    assert result.success is False
    assert result.error_message is not None
    assert "fatal error" in result.error_message


class TestEngineIntegration:
    """Integration-level tests for SimulationEngine.run().

    These tests define the expected engine behaviour for end-to-end scenarios.
    """

    def test_minimal_single_turn_scenario_returns_success(self):
        """A scenario with one person and one account and no flows produces at least one turn.

        The engine must produce a SimulationResult where result.turns has at least
        one entry and result.success is True when no flows signal an error.
        """
        from fitinera.models import Age, Person

        config = EngineConfiguration(
            start_date=Date(2026, 1), max_turns=TurnDuration(1, 0)
        )
        engine = SimulationEngine(config)
        scenario = SimulationScenario(
            initial_persons=[Person(id="p1", age=Age(30), expectancy=Age(90))],
            initial_accounts=[Account(id="checking", initial_balance=1000.0)],
        )

        result = engine.run(scenario)

        assert len(result.turns) >= 1
        assert result.success is True

    def test_solvency_guard_flow_triggers_failure_on_negative_balance(self):
        """AccountSolvencyGuardFlow causes result.success to be False when an ASSET account is negative.

        When AccountSolvencyGuardFlow is included in the pipeline and the initial
        balance of an ASSET-labeled account is negative, the engine must halt and return
        a SimulationResult where result.success is False.
        """
        config = EngineConfiguration(
            start_date=Date(2026, 1),
            max_turns=TurnDuration(1, 0),
            flows=[AccountSolvencyGuardFlow()],
        )
        engine = SimulationEngine(config)
        scenario = SimulationScenario(
            initial_accounts=[
                Account(id="checking", initial_balance=-500.0, labels={"Type": "ASSET"})
            ],
        )

        result = engine.run(scenario)

        assert result.success is False


def test_engine_halts_when_living_expense_drains_account_negative():
    """Engine halts with success=False when LivingExpenseFlow drains account below zero."""
    config = EngineConfiguration(
        start_date=Date(2026, 1),
        max_turns=TurnDuration(1, 0),
        flows=[
            LivingExpenseFlow(from_account="checking", amount=200.0),
            AccountSolvencyGuardFlow(),
        ],
    )
    engine = SimulationEngine(config)
    scenario = SimulationScenario(
        initial_accounts=[
            Account(id="checking", initial_balance=100.0, labels={"Type": "ASSET"})
        ],
    )

    result = engine.run(scenario)

    assert result.success is False


def test_engine_halts_with_solvency_error_message_containing_account_id():
    """Solvency failure error message identifies the insolvent account by id."""
    config = EngineConfiguration(
        start_date=Date(2026, 1),
        max_turns=TurnDuration(1, 0),
        flows=[
            LivingExpenseFlow(from_account="checking", amount=200.0),
            AccountSolvencyGuardFlow(),
        ],
    )
    engine = SimulationEngine(config)
    scenario = SimulationScenario(
        initial_accounts=[
            Account(id="checking", initial_balance=100.0, labels={"Type": "ASSET"})
        ],
    )

    result = engine.run(scenario)

    assert result.error_message is not None
    assert "checking" in result.error_message


def test_simulation_result_log_messages_contains_turn_messages():
    """SimulationResult.log_messages captures messages emitted during turns."""

    class _InfoFlow:
        def executeFlow(self, view, updater, logger):
            logger.info("turn ran")

    config = EngineConfiguration(
        start_date=Date(2026, 1),
        max_turns=TurnDuration(0, 1),
        flows=[_InfoFlow()],
    )
    engine = SimulationEngine(config)
    scenario = SimulationScenario()

    result = engine.run(scenario)

    assert any("turn ran" in m for m in result.log_messages)


def test_simulation_result_log_messages_includes_error_turn_messages():
    """log_messages includes messages from the error turn even when simulation halts."""

    class _ErrorFlow:
        def executeFlow(self, view, updater, logger):
            logger.warning("pre-error warning")
            logger.error("fatal halt")

    config = EngineConfiguration(
        start_date=Date(2026, 1),
        max_turns=TurnDuration(1, 0),
        flows=[_ErrorFlow()],
    )
    engine = SimulationEngine(config)
    scenario = SimulationScenario()

    result = engine.run(scenario)

    assert result.success is False
    assert any("pre-error warning" in m for m in result.log_messages)
    assert any("fatal halt" in m for m in result.log_messages)
