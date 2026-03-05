from .interfaces import Flow
from ..engine.interfaces import (
    SimulationStateView,
    SimulationStateUpdater,
    SimulationLogger,
)


class MortgagePaymentFlow(Flow):
    """Handles a fixed regular mortgage or loan payment between two accounts each turn."""

    def __init__(self, from_account: str, to_account: str, amount: float):
        self.from_account = from_account
        self.to_account = to_account
        self.amount = amount

    def executeFlow(
        self,
        view: SimulationStateView,
        updater: SimulationStateUpdater,
        logger: SimulationLogger,
    ) -> None:
        raise NotImplementedError("Pending implementation")
