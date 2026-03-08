from .interfaces import MetricGenerator
from ..engine.interfaces import SimulationLogger, SimulationStateView


class NetWorthGenerator(MetricGenerator):
    """Calculates net worth by summing the balances of all accounts unconditionally.

    Convention: ASSET accounts carry positive balances; LIABILITY accounts carry negative
    balances (e.g. a $300,000 mortgage is stored as -300,000.0). Net worth is the sum of
    every account balance regardless of labels.
    """

    def evaluate(self, view: SimulationStateView, _logger: SimulationLogger) -> float:
        """Return the sum of all account balances in the current state.

        Args:
            view: Read-only interface to the current simulation state.
            logger: Logger (unused by this generator; retained for interface compliance).

        Returns:
            Net worth as a float — the sum of every account's balance.
        """
        return sum(account.balance for account in view.get_accounts())
