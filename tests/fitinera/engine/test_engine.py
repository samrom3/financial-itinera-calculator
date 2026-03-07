import pytest
from fitinera.engine import SimulationEngine, EngineConfiguration
from fitinera.flows import AccountSolvencyGuardFlow
from fitinera.models import Account, SimulationScenario, Date, TurnDuration
from fitinera import SimulationResult


def test_simulation_engine_initialization_takes_configuration():
    config = EngineConfiguration(Date(2026, 1), TurnDuration(10, 0))
    engine = SimulationEngine(config)
    assert engine.configuration is config


def test_engine_run_raises_not_implemented():
    config = EngineConfiguration(Date(2026, 1), TurnDuration(10, 0))
    engine = SimulationEngine(config)
    scenario = SimulationScenario()
    with pytest.raises(NotImplementedError):
        engine.run(scenario)


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


@pytest.mark.skip(reason="Not yet implemented")
def test_engine_halts_on_logger_error():
    pass


class TestEngineIntegration:
    """Integration-level tests for SimulationEngine.run().

    These tests define the expected engine behaviour for end-to-end scenarios.
    They are expected to fail with NotImplementedError until story-10 wires the
    engine internals, and are therefore marked xfail.
    """

    @pytest.mark.xfail(
        raises=NotImplementedError,
        strict=True,
        reason="Pending story-10 engine implementation",
    )
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

    @pytest.mark.xfail(
        raises=NotImplementedError,
        strict=True,
        reason="Pending story-10 engine implementation",
    )
    def test_solvency_guard_flow_triggers_failure_on_negative_balance(self):
        """AccountSolvencyGuardFlow causes result.success to be False when checking account is negative.

        When AccountSolvencyGuardFlow is included in the pipeline and the initial
        balance of the guarded account is negative, the engine must halt and return
        a SimulationResult where result.success is False.
        """
        config = EngineConfiguration(
            start_date=Date(2026, 1),
            max_turns=TurnDuration(1, 0),
            flows=[AccountSolvencyGuardFlow()],
        )
        engine = SimulationEngine(config)
        scenario = SimulationScenario(
            initial_accounts=[Account(id="checking", initial_balance=-500.0)],
        )

        result = engine.run(scenario)

        assert result.success is False
