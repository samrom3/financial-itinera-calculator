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
        """Create a living expense flow.

        Args:
            from_account: ID of the account from which the expense is debited each turn.
            amount: Base expense amount (in currency units) before inflation adjustment.
            annual_inflation_rate: Annualised inflation rate applied to the base amount
                each turn (default 0.0 — fixed expense). Negative values model deflation.
        """
        self._from_account = from_account
        self._amount = amount
        self._annual_inflation_rate = annual_inflation_rate

    def executeFlow(
        self,
        view: SimulationStateView,
        updater: SimulationStateUpdater,
        logger: SimulationLogger,
    ) -> None:
        """Emit a living expense, applying inflation or deflation if annual_inflation_rate != 0.

        When annual_inflation_rate is 0.0, emits a fixed expense equal to self.amount.
        When annual_inflation_rate != 0, computes the adjusted amount using the effective
        annual rate formula:
            inflated_amount = amount * (1 + annual_inflation_rate) ** (turn_index / 12.0)
        where turn_index = view.get_elapsed_duration().months (FR-019). This matches the
        effective annual rate convention used by AccountInterestFlow. Negative rates model
        deflation (decreasing expenses over time).
        """
        if self._annual_inflation_rate != 0.0:
            turn_index = view.get_elapsed_duration().months
            inflated_amount = self._amount * (1 + self._annual_inflation_rate) ** (
                turn_index / 12.0
            )
            updater.emit_transaction(
                Expense(amount=inflated_amount, from_account=self._from_account)
            )
        else:
            updater.emit_transaction(
                Expense(amount=self._amount, from_account=self._from_account)
            )
