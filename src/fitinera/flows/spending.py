from .interfaces import Flow
from ..engine.interfaces import (
    SimulationStateView,
    SimulationStateUpdater,
    SimulationLogger,
)
from ..models.transaction import Expense


class LivingExpenseFlow(Flow):
    """Records a fixed recurring living expense drawn from a specified account each turn."""

    def __init__(
        self, from_account: str, amount: float, annual_inflation_rate: float = 0.0
    ):
        self.from_account = from_account
        self.amount = amount
        self.annual_inflation_rate = annual_inflation_rate

    def executeFlow(
        self,
        view: SimulationStateView,
        updater: SimulationStateUpdater,
        logger: SimulationLogger,
    ) -> None:
        """Emit a fixed living expense; inflation path not yet implemented."""
        updater.emit_transaction(
            Expense(amount=self.amount, from_account=self.from_account)
        )
