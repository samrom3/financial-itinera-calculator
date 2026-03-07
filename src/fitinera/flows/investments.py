"""Investment-domain flows and strategies for the fitinera engine.

Provides:
  - MinSavingsStrategy: Protocol for minimum-savings computation.
  - CurrentTurnExpenseStrategy: computes minimum from current turn expenses.
  - RollingAverageExpenseStrategy: computes minimum from a rolling average.
  - AccountInterestFlow: applies periodic interest to an account.
  - RebalanceExtraSavingsFlow: moves excess savings from one account to another.
"""

from typing import Protocol

from .interfaces import Flow
from ..engine.interfaces import (
    SimulationStateView,
    SimulationStateUpdater,
    SimulationLogger,
)


class MinSavingsStrategy(Protocol):
    """Protocol defining a strategy to compute a minimum savings amount.

    Implementing classes must provide a ``compute_minimum`` method that
    inspects the current simulation state and returns the minimum float
    amount that should remain in the source account.
    """

    def compute_minimum(self, view: SimulationStateView, from_account: str) -> float:
        """Compute the minimum balance that must remain in from_account.

        Args:
            view: Read-only view of the current simulation state.
            from_account: Account identifier whose minimum is being computed.

        Returns:
            The minimum float amount to retain in the account.
        """
        raise NotImplementedError("Pending implementation")


class CurrentTurnExpenseStrategy:
    """Computes minimum savings based on current-turn expenses times a multiplier.

    Args:
        expense_multiplier: Multiplier applied to current turn's total expenses.
            Defaults to 3.0 (three months of expenses).
    """

    def __init__(self, expense_multiplier: float = 3.0):
        self.expense_multiplier = expense_multiplier

    def compute_minimum(self, view: SimulationStateView, from_account: str) -> float:
        """Compute minimum as current-turn expenses multiplied by expense_multiplier.

        Args:
            view: Read-only view of the current simulation state.
            from_account: Account identifier whose minimum is being computed.

        Returns:
            Minimum balance to retain.
        """
        raise NotImplementedError("Pending implementation")


class RollingAverageExpenseStrategy:
    """Computes minimum savings based on a rolling average of past expenses.

    Args:
        lookback_months: Number of months to include in the rolling average.
        expense_multiplier: Multiplier applied to the rolling average.
            Defaults to 3.0 (three months of expenses).
    """

    def __init__(self, lookback_months: int, expense_multiplier: float = 3.0):
        self.lookback_months = lookback_months
        self.expense_multiplier = expense_multiplier

    def compute_minimum(self, view: SimulationStateView, from_account: str) -> float:
        """Compute minimum as rolling-average expenses multiplied by expense_multiplier.

        Args:
            view: Read-only view of the current simulation state.
            from_account: Account identifier whose minimum is being computed.

        Returns:
            Minimum balance to retain.
        """
        raise NotImplementedError("Pending implementation")


class AccountInterestFlow(Flow):
    """Applies periodic interest to an account each simulation turn.

    Args:
        account_id: Identifier of the account to apply interest to.
        annual_rate: Annual interest rate as a decimal (e.g. 0.05 for 5%).
    """

    def __init__(self, account_id: str, annual_rate: float):
        self.account_id = account_id
        self.annual_rate = annual_rate

    def executeFlow(
        self,
        view: SimulationStateView,
        updater: SimulationStateUpdater,
        logger: SimulationLogger,
    ) -> None:
        raise NotImplementedError("Pending implementation")


class RebalanceExtraSavingsFlow(Flow):
    """Moves excess savings from a source account to a destination account.

    Excess savings are the amount above the minimum required balance as
    determined by the provided strategy.

    Args:
        from_account: Source account identifier (where excess savings live).
        to_account: Destination account identifier (where excess is moved).
        strategy: Strategy used to compute the minimum balance to retain
            in from_account.
    """

    def __init__(
        self,
        from_account: str,
        to_account: str,
        strategy: MinSavingsStrategy,
    ):
        self.from_account = from_account
        self.to_account = to_account
        self.strategy = strategy

    def executeFlow(
        self,
        view: SimulationStateView,
        updater: SimulationStateUpdater,
        logger: SimulationLogger,
    ) -> None:
        raise NotImplementedError("Pending implementation")
