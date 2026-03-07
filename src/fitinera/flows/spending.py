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
        """Emit a living expense, applying inflation if annual_inflation_rate > 0.

        When annual_inflation_rate is 0.0, emits a fixed expense equal to self.amount.
        When annual_inflation_rate > 0, computes the inflated amount as:
            inflated_amount = amount * (1 + annual_inflation_rate / 12) ** turn_index
        where turn_index = view.get_elapsed_duration().months (FR-019).
        """
        if self.annual_inflation_rate > 0.0:
            turn_index = view.get_elapsed_duration().months
            inflated_amount = (
                self.amount * (1 + self.annual_inflation_rate / 12) ** turn_index
            )
            updater.emit_transaction(
                Expense(amount=inflated_amount, from_account=self.from_account)
            )
        else:
            updater.emit_transaction(
                Expense(amount=self.amount, from_account=self.from_account)
            )
