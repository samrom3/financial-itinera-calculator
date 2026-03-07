import pytest
from fitinera.engine import SimulationEngine, EngineConfiguration
from fitinera.models import SimulationScenario, Date, TurnDuration
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
