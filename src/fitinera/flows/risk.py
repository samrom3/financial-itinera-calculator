from typing import Optional

from .interfaces import Flow
from ..engine.interfaces import (
    SimulationStateView,
    SimulationStateUpdater,
    SimulationLogger,
)
from ..engine.result import FitineraError, SolvencyViolationError
from ..models.account import AssetAccountState


class AssetSolvencyGuardFlow(Flow):
    """Monitors asset accounts and halts simulation when a solvency violation is detected.

    Returns a SolvencyViolationError when an AssetAccountState instance has a
    negative balance, signaling the engine to halt and embed the error in
    SimulationData.result. Guards are applied by type, not by label lookup.
    """

    def executeFlow(
        self,
        view: SimulationStateView,
        updater: SimulationStateUpdater,
        logger: SimulationLogger,
    ) -> Optional[FitineraError]:
        """Return SolvencyViolationError for the first AssetAccountState with a negative balance.

        Returns:
            SolvencyViolationError: When an AssetAccountState has a negative balance,
                with the account ID and balance in the message.
            None: When all AssetAccountState instances have non-negative balances.
        """
        for account in view.get_accounts():
            if isinstance(account, AssetAccountState) and account.balance < 0:
                return SolvencyViolationError(
                    f"Account '{account.id}' has negative balance: {account.balance}"
                )
        return None
