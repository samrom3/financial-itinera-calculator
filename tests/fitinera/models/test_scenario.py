import pytest
from fitinera.models import Account, Age, Date, Metric, Person, SimulationScenario, Turn


def test_turn_contains_immutable_snapshot_of_state():
    person = Person(id="p1", age=Age(years=30), expectancy=Age(years=80))
    account = Account(id="a1", initial_balance=1000.0)
    metric = Metric(name="net_worth", value=1000.0)
    turn = Turn(
        date=Date(year=2026, month=1),
        accounts=[account],
        persons=[person],
        transactions=[],
        metrics=[metric],
    )
    with pytest.raises((AttributeError, TypeError)):
        turn.date = Date(year=2027, month=1)  # type: ignore[misc]


def test_simulation_scenario_can_be_initialized_with_empty_lists():
    scenario = SimulationScenario()
    assert scenario.initial_persons == []
    assert scenario.initial_accounts == []


def test_simulation_scenario_holds_initial_persons_and_accounts():
    person = Person(id="p1", age=Age(years=30), expectancy=Age(years=80))
    account = Account(id="a1", initial_balance=500.0)
    scenario = SimulationScenario(initial_persons=[person], initial_accounts=[account])
    assert scenario.initial_persons == [person]
    assert scenario.initial_accounts == [account]
