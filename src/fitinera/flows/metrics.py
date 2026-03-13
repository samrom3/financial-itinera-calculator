from .interfaces import MetricGenerator
from ..engine.interfaces import SimulationLogger, SimulationStateView
from ..models.account import AssetAccountState, LiabilityAccountState


class NetWorthGenerator(MetricGenerator):
    """Calculates net worth as total assets minus total liabilities.

    Convention: both asset and liability balances are stored as positive values.
    Net worth = sum(asset balances) - sum(liability balances).
    """

    def evaluate(self, view: SimulationStateView, _logger: SimulationLogger) -> float:
        """Return assets minus liabilities for all accounts in the current state.

        Args:
            view: Read-only interface to the current simulation state.
            _logger: Logger (unused by this generator; retained for interface compliance).

        Returns:
            Net worth as a float — total asset balances minus total liability balances.
        """
        accounts = view.get_accounts()
        assets = sum(a.balance for a in accounts if isinstance(a, AssetAccountState))
        liabilities = sum(
            a.balance for a in accounts if isinstance(a, LiabilityAccountState)
        )
        return assets - liabilities
