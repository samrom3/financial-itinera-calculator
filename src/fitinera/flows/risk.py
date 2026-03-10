from .interfaces import Flow
from ..engine.interfaces import (
    SimulationStateView,
    SimulationStateUpdater,
    SimulationLogger,
)
from ..engine.exceptions import SolvencyViolationError


class AccountSolvencyGuardFlow(Flow):
    """Monitors accounts and halts simulation when a solvency violation is detected.

    Raises:
        SolvencyViolationError: When an ASSET-labeled account has a negative balance.

    Args:
        asset_label_facet: Label facet used to identify account type.
            Defaults to 'Type'.
        asset_label_value: Label value that marks an account as an asset to guard.
            Defaults to 'ASSET'.
    """

    def __init__(
        self,
        asset_label_facet: str = "Type",
        asset_label_value: str = "ASSET",
    ):
        self.asset_label_facet = asset_label_facet
        self.asset_label_value = asset_label_value

    def executeFlow(
        self,
        view: SimulationStateView,
        updater: SimulationStateUpdater,
        logger: SimulationLogger,
    ) -> None:
        """Raise SolvencyViolationError for each ASSET-labeled account with a negative balance."""
        for account in view.get_accounts():
            if account.get_label(self.asset_label_facet) == self.asset_label_value:
                if account.balance < 0:
                    raise SolvencyViolationError(
                        f"Account '{account.id}' has negative balance: {account.balance}"
                    )
