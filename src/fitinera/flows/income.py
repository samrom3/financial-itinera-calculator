from .interfaces import Flow
from ..engine.interfaces import (
    SimulationStateView,
    SimulationStateUpdater,
    SimulationLogger,
)


class JobIncomeFlow(Flow):
    """Injects regular employment income for a person each turn they are actively working."""

    def __init__(self, person_id: str, amount: float, to_account: str):
        self.person_id = person_id
        self.amount = amount
        self.to_account = to_account

    def executeFlow(
        self,
        view: SimulationStateView,
        updater: SimulationStateUpdater,
        logger: SimulationLogger,
    ) -> None:
        raise NotImplementedError("Pending implementation")
