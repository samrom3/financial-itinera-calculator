from fitinera.models import SimulationScenario


def test_turn_contains_immutable_snapshot_of_state():
    pass


def test_simulation_scenario_can_be_initialized_with_empty_lists():
    scenario = SimulationScenario()
    assert scenario.initial_persons == []
    assert scenario.initial_accounts == []


def test_simulation_scenario_holds_initial_persons_and_accounts():
    pass
