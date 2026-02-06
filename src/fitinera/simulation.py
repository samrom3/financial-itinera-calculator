from .planning import FinancialScenario
from .results import SimulationResult, SimulationStatus
from .turn_handler import TurnHandler, TurnState


class Simulator:
    """Runs a financial simulation based on a given scenario."""

    def run(self, scenario: FinancialScenario) -> SimulationResult:
        """
        Runs the simulation and returns the results.

        :param scenario: The financial scenario to simulate.
        :return: A SimulationResult object containing the outcome of the simulation.
        """
        history = []

        turn_state = TurnState(scenario)
        turn_handler = TurnHandler()

        while turn_state.current_age < scenario.time_horizon.life_expectancy:
            turn_result = turn_handler.run(scenario=scenario, turn_state=turn_state)
            history.append(turn_result)

            if sum(turn_result.next_asset_breakdown.values()) <= 0:
                is_retired = (
                    turn_state.current_age >= scenario.retirement_goal.retirement_age
                )
                status = (
                    SimulationStatus.PRE_RETIREMENT_BANKRUPTCY
                    if not is_retired
                    else SimulationStatus.POST_RETIREMENT_BANKRUPTCY
                )
                return SimulationResult(
                    status=status, history=history, scenario=scenario
                )

            turn_state.current_age = turn_state.current_age.next_month()

        # Final check for estate goal
        final_assets = sum(a.initial_value for a in turn_state.assets.values())
        if final_assets < scenario.retirement_goal.desired_estate_value:
            status = SimulationStatus.INSUFFICIENT_ESTATE
        else:
            status = SimulationStatus.SUCCESS

        return SimulationResult(status=status, history=history, scenario=scenario)
