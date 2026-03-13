from .interfaces import Flow
from ..engine.interfaces import (
    SimulationStateView,
    SimulationStateUpdater,
    SimulationLogger,
)
from ..models.transaction import Transfer


class SimpleMortgagePaymentFlow(Flow):
    """Handles a fixed regular mortgage or loan payment between two accounts each turn.

    This flow models principal-only payments — interest is not split out.
    Each turn it emits a single Transfer of the configured amount from the
    source account to the mortgage account, reducing the outstanding balance.

    For realistic fixed-rate amortization schedules that split each payment
    into interest (Expense) and principal (Transfer) components, use
    ``AmortizingFixedInterestMortgageFlow`` (planned — see
    https://github.com/samrom3/financial-itinera-calculator/issues/33).
    """

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
        """Emit a fixed transfer from the source account to the mortgage account."""
        updater.emit_transaction(
            Transfer(
                amount=self.amount,
                from_account=self.from_account,
                to_account=self.to_account,
            )
        )
