from fitinera.engine import EngineConfiguration
from fitinera.engine.listeners import PythonLoggingListener
from fitinera.models import Date, TurnDuration


def test_engine_configuration_holds_start_date_and_max_turns():
    config = EngineConfiguration(Date(2026, 1), TurnDuration.of(years=10))
    assert config.start_date.year == 2026


def test_engine_configuration_defaults_metrics_and_flows_to_empty():
    config = EngineConfiguration(Date(2026, 1), TurnDuration.of(years=10))
    assert config.metrics == {}
    assert config.flows == []


def test_engine_configuration_defaults_log_listeners_to_python_logging_listener():
    """log_listeners defaults to a list containing one PythonLoggingListener."""
    config = EngineConfiguration(Date(2026, 1), TurnDuration.of(years=10))
    assert len(config.log_listeners) == 1
    assert isinstance(config.log_listeners[0], PythonLoggingListener)


def test_engine_configuration_accepts_custom_log_listeners():
    """log_listeners can be overridden with custom listener instances."""
    from fitinera.engine.listeners import ListLogListener

    listener = ListLogListener()
    config = EngineConfiguration(
        Date(2026, 1), TurnDuration.of(years=10), log_listeners=[listener]
    )
    assert config.log_listeners == [listener]


def test_engine_configuration_log_listeners_default_is_independent_per_instance():
    """Each EngineConfiguration instance gets its own default log_listeners list."""
    config1 = EngineConfiguration(Date(2026, 1), TurnDuration.of(years=10))
    config2 = EngineConfiguration(Date(2026, 1), TurnDuration.of(years=10))
    assert config1.log_listeners is not config2.log_listeners
