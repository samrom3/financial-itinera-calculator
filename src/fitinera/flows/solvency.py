from .interfaces import Flow
from ..engine.interfaces import (
    SimulationStateView,
    SimulationStateUpdater,
    SimulationLogger,
)


class AccountSolvencyGuardFlow(Flow):
    """Halts the simulation via the logger when any account has a negative balance."""

    def __init__(self, account_id: str):
        self.account_id = account_id

    def executeFlow(
        self,
        view: SimulationStateView,
        updater: SimulationStateUpdater,
        logger: SimulationLogger,
    ) -> None:
        raise NotImplementedError("Pending implementation")
