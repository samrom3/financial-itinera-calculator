from .interfaces import Flow
from ..engine.interfaces import (
    SimulationStateView,
    SimulationStateUpdater,
    SimulationLogger,
)


class LivingExpenseFlow(Flow):
    """Records a fixed recurring living expense drawn from a specified account each turn."""

    def __init__(self, from_account: str, amount: float):
        self.from_account = from_account
        self.amount = amount

    def executeFlow(
        self,
        view: SimulationStateView,
        updater: SimulationStateUpdater,
        logger: SimulationLogger,
    ) -> None:
        raise NotImplementedError("Pending implementation")
