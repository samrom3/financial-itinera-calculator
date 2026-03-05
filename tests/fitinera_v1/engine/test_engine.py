import pytest
from fitinera_v1.engine import SimulationEngine, EngineConfiguration
from fitinera_v1.models import SimulationScenario, Date, TurnDuration


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


def test_engine_halts_on_logger_error():
    pass
