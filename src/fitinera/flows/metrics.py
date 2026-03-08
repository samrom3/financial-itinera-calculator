from .interfaces import MetricGenerator
from ..engine.interfaces import SimulationLogger, SimulationStateView


class NetWorthGenerator(MetricGenerator):
    """Calculates global net worth as total ASSET balances minus total LIABILITY balances."""

    def evaluate(self, view: SimulationStateView, logger: SimulationLogger) -> float:
        """Sums ASSET balances and subtracts LIABILITY balances across all accounts.

        Accounts without a 'Type' label, or with an unrecognised Type value,
        are ignored and do not affect the result.

        Args:
            view: Read-only interface to the current simulation state.
            logger: Logger for reporting anomalies (e.g. unrecognised account types).

        Returns:
            Net worth as a float (assets minus liabilities).
        """
        net_worth = 0.0
        for account in view.get_accounts():
            account_type = account.get_label("Type")
            if account_type == "ASSET":
                net_worth += account.balance
            elif account_type == "LIABILITY":
                net_worth -= account.balance
            elif account_type is not None:
                logger.warning(
                    f"NetWorthGenerator: account '{account.id}' has unrecognised "
                    f"Type label '{account_type}'; excluded from net worth calculation."
                )
        return net_worth
