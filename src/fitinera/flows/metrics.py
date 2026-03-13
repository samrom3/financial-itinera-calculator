from .interfaces import MetricGenerator
from ..engine.interfaces import SimulationLogger, SimulationStateView
from ..models.account import AssetAccountState, LiabilityAccountState


class NetWorthGenerator(MetricGenerator):
    """Calculates net worth as total assets minus total liabilities.

    Convention: both asset and liability balances are stored as positive values.
    Net worth = sum(asset balances) - sum(liability balances).
    """

    def evaluate(self, view: SimulationStateView, logger: SimulationLogger) -> float:
        """Return assets minus liabilities for all accounts in the current state.

        Args:
            view: Read-only interface to the current simulation state.
            logger: Logger for recording any relevant messages during metric evaluation.

        Returns:
            Net worth as a float — total asset balances minus total liability balances.
        """
        total_net_worth = 0.0
        for a in view.get_accounts():
            if isinstance(a, AssetAccountState):
                total_net_worth += a.balance
            elif isinstance(a, LiabilityAccountState):
                total_net_worth -= a.balance
            else:
                logger.error(
                    f"NetWorthGenerator: Unrecognized account type for account '{a.id}'"
                )
        return total_net_worth
