import copy

from .planning import FinancialScenario
from .results import SimulationResult, SimulationStatus
from .turn_handler import TurnHandler


class Simulator:
    """Runs a financial simulation based on a given scenario."""

    def run(self, scenario: FinancialScenario) -> SimulationResult:
        """
        Runs the simulation and returns the results.

        :param scenario: The financial scenario to simulate.
        :return: A SimulationResult object containing the outcome of the simulation.
        """
        history = []
        assets = copy.deepcopy(scenario.assets)
        incomes = copy.deepcopy(scenario.incomes)
        expenses = copy.deepcopy(scenario.expenses)
        tax_rates = scenario.tax_rates[:]
        current_age = scenario.time_horizon.current_age

        turn_handler = TurnHandler()

        while current_age < scenario.time_horizon.life_expectancy:
            turn_result, assets, incomes, expenses = turn_handler.run(
                scenario, current_age, assets, incomes, expenses, tax_rates
            )
            history.append(turn_result)

            if sum(turn_result.next_asset_breakdown.values()) <= 0:
                is_retired = current_age >= scenario.retirement_goal.retirement_age
                status = (
                    SimulationStatus.PRE_RETIREMENT_BANKRUPTCY
                    if not is_retired
                    else SimulationStatus.POST_RETIREMENT_BANKRUPTCY
                )
                return SimulationResult(
                    status=status, history=history, scenario=scenario
                )

            current_age = current_age.next_month()

        # Final check for estate goal
        final_assets = sum(a.initial_value for a in assets)
        if final_assets < scenario.retirement_goal.desired_estate_value:
            status = SimulationStatus.INSUFFICIENT_ESTATE
        else:
            status = SimulationStatus.SUCCESS

        return SimulationResult(status=status, history=history, scenario=scenario)
