import pytest
from fitinera.engine import SimulationEngine, EngineConfiguration
from fitinera.engine.result import (
    ReachedMaxTurns,
    SolvencyViolationError,
)
from fitinera.flows import AssetSolvencyGuardFlow, LivingExpenseFlow
from fitinera.models import AssetAccount, SimulationScenario, Date, TurnDuration
from fitinera import SimulationData


def test_simulation_engine_initialization_takes_configuration():
    config = EngineConfiguration(Date(2026, 1), TurnDuration.of(years=10))
    engine = SimulationEngine(config)
    assert engine.configuration is config


class TestSimulationDataShape:
    """Tests verifying SimulationData dataclass shape and field types.

    These tests confirm that SimulationData is a frozen dataclass with
    a result field and a turns field.
    """

    def test_simulation_data_can_be_constructed_with_result_and_turns(self):
        """SimulationData accepts a result and a turns list at construction."""
        data = SimulationData(result=ReachedMaxTurns(), turns=[])
        assert data.turns == []
        assert data.result.ok()

    def test_simulation_data_turns_defaults_to_empty_list(self):
        """SimulationData.turns defaults to an empty list when not provided."""
        data = SimulationData(result=ReachedMaxTurns())
        assert data.turns == []

    def test_simulation_data_is_frozen(self):
        """SimulationData is immutable; field assignment raises FrozenInstanceError."""
        data = SimulationData(result=ReachedMaxTurns(), turns=[])
        with pytest.raises(Exception):
            data.turns = []  # type: ignore[misc]

    def test_simulation_data_turns_field_accepts_list(self):
        """SimulationData.turns is a list, indexable and iterable."""
        data = SimulationData(result=ReachedMaxTurns(), turns=[])
        assert isinstance(data.turns, list)
        assert len(data.turns) == 0

    def test_simulation_data_result_field_is_fitinera_result(self):
        """SimulationData.result holds a FitineraResult instance."""
        from fitinera.engine.result import FitineraResult

        data = SimulationData(result=ReachedMaxTurns())
        assert isinstance(data.result, FitineraResult)


def test_engine_returns_solvency_violation_in_result_on_negative_balance():
    """Engine returns SimulationData with SolvencyViolationError when an ASSET account is negative."""
    from fitinera.models import Age, Person

    config = EngineConfiguration(
        start_date=Date(2026, 1),
        max_turns=TurnDuration.of(years=1),
        flows=[AssetSolvencyGuardFlow()],
    )
    engine = SimulationEngine(config)
    scenario = SimulationScenario(
        initial_persons=[Person(id="p1", age=Age(30), expectancy=Age(90))],
        initial_accounts=[
            AssetAccount(id="checking", balance=-500.0, labels={"Type": "ASSET"})
        ],
    )

    data = engine.run(scenario)

    assert not data.result.ok()
    assert isinstance(data.result, SolvencyViolationError)


class TestEngineIntegration:
    """Integration-level tests for SimulationEngine.run().

    These tests define the expected engine behaviour for end-to-end scenarios.
    """

    def test_minimal_single_turn_scenario_returns_turns(self):
        """A scenario with one person and one account and no flows produces at least one turn.

        The engine must produce a SimulationData where data.turns has at least
        one entry when no flows return an error.
        """
        from fitinera.models import Age, Person

        config = EngineConfiguration(
            start_date=Date(2026, 1), max_turns=TurnDuration.of(years=1)
        )
        engine = SimulationEngine(config)
        scenario = SimulationScenario(
            initial_persons=[Person(id="p1", age=Age(30), expectancy=Age(90))],
            initial_accounts=[AssetAccount(id="checking", balance=1000.0)],
        )

        data = engine.run(scenario)

        assert len(data.turns) >= 1
        assert data.result.ok()

    def test_solvency_guard_flow_returns_error_on_negative_balance(self):
        """AssetSolvencyGuardFlow triggers a SolvencyViolationError in SimulationData.result.

        When AssetSolvencyGuardFlow is included in the pipeline and the initial
        balance of an ASSET-labeled account is negative, SimulationData.result
        holds a SolvencyViolationError.
        """
        config = EngineConfiguration(
            start_date=Date(2026, 1),
            max_turns=TurnDuration.of(years=1),
            flows=[AssetSolvencyGuardFlow()],
        )
        engine = SimulationEngine(config)
        scenario = SimulationScenario(
            initial_accounts=[
                AssetAccount(id="checking", balance=-500.0, labels={"Type": "ASSET"})
            ],
        )

        data = engine.run(scenario)

        assert not data.result.ok()
        assert isinstance(data.result, SolvencyViolationError)


def test_engine_returns_solvency_error_when_living_expense_drains_account_negative():
    """Engine returns SolvencyViolationError in result when LivingExpenseFlow drains account below zero."""
    config = EngineConfiguration(
        start_date=Date(2026, 1),
        max_turns=TurnDuration.of(years=1),
        flows=[
            LivingExpenseFlow(from_account="checking", amount=200.0),
            AssetSolvencyGuardFlow(),
        ],
    )
    engine = SimulationEngine(config)
    scenario = SimulationScenario(
        initial_accounts=[
            AssetAccount(id="checking", balance=100.0, labels={"Type": "ASSET"})
        ],
    )

    data = engine.run(scenario)

    assert not data.result.ok()
    assert isinstance(data.result, SolvencyViolationError)


def test_engine_solvency_error_message_contains_account_id():
    """Solvency violation error message identifies the insolvent account by id."""
    config = EngineConfiguration(
        start_date=Date(2026, 1),
        max_turns=TurnDuration.of(years=1),
        flows=[
            LivingExpenseFlow(from_account="checking", amount=200.0),
            AssetSolvencyGuardFlow(),
        ],
    )
    engine = SimulationEngine(config)
    scenario = SimulationScenario(
        initial_accounts=[
            AssetAccount(id="checking", balance=100.0, labels={"Type": "ASSET"})
        ],
    )

    data = engine.run(scenario)

    assert not data.result.ok()
    assert "checking" in data.result.message()


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

    data = engine.run(scenario)

    assert len(data.turns) == 1
    assert data.result.ok()
