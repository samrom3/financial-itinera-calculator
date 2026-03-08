from fitinera.engine import EngineConfiguration
from fitinera.models import Date, TurnDuration


def test_engine_configuration_holds_start_date_and_max_turns():
    config = EngineConfiguration(Date(2026, 1), TurnDuration.of(years=10))
    assert config.start_date.year == 2026


def test_engine_configuration_defaults_metrics_and_flows_to_empty():
    config = EngineConfiguration(Date(2026, 1), TurnDuration.of(years=10))
    assert config.metrics == {}
    assert config.flows == []
