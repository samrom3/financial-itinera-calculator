"""Internal engine state implementations.

These classes are private implementation details of the engine and are not
exported from the fitinera public API. They implement the Protocol interfaces
defined in interfaces.py and are wired up by SimulationEngine.run().
"""

import dataclasses
from typing import Any, Dict, List, Optional

from ..models import AccountState, Date, Person, Transaction, TurnDuration
from ..models.transaction import Expense, Income, Transfer
from .interfaces import (
    LogListener,
    SimulationLogger,
    SimulationStateUpdater,
    SimulationStateView,
)


class _SimulationStateViewImpl(SimulationStateView):
    """Internal implementation of SimulationStateView.

    Holds references to the live engine state and exposes read-only access
    to flows during a simulation turn.
    """

    def __init__(
        self,
        account_states: List[AccountState],
        person_states: Dict[str, "_LivePersonState"],
        metric_generators: Dict[str, Any],
        start_date: Date,
        current_date_ref: "list[Date]",
        turns_completed_ref: "list[int]",
        tx_buffer: "list[Transaction]",
        logger: SimulationLogger,
    ) -> None:
        self._accounts = account_states
        self._persons = person_states
        self._metrics = metric_generators
        self._start_date = start_date
        self._current_date_ref = current_date_ref
        self._turns_completed_ref = turns_completed_ref
        self._tx_buffer = tx_buffer
        self._logger = logger

    def get_accounts(self) -> List[AccountState]:
        """Return live AccountState objects for all accounts."""
        return list(self._accounts)

    def get_person(self, person_id: str) -> Optional[Person]:
        """Return a frozen Person snapshot built from live state, or None."""
        state = self._persons.get(person_id)
        if state is None:
            return None
        return dataclasses.replace(
            state.person, age=state.age, labels=dict(state.labels)
        )

    def get_metric(self, name: str) -> Any:
        """Lazily evaluate the named MetricGenerator and return its value."""
        generator = self._metrics.get(name)
        if generator is None:
            return None
        return generator.evaluate(self, self._logger)

    def get_start_date(self) -> Date:
        """Return the simulation start date from EngineConfiguration."""
        return self._start_date

    def get_current_date(self) -> Date:
        """Return the current (post-increment) date for this turn."""
        return self._current_date_ref[0]

    def get_elapsed_duration(self) -> TurnDuration:
        """Return elapsed months since simulation start (turns completed so far)."""
        return TurnDuration(months=self._turns_completed_ref[0])

    def get_current_turn_transactions(self) -> List[Transaction]:
        """Return transactions emitted during the current turn."""
        return list(self._tx_buffer)


class _LivePersonState:
    """Mutable live state for a single person tracked by the engine."""

    def __init__(self, person: Person) -> None:
        self.person = person
        self.age = dataclasses.replace(person.age)
        self.labels: Dict[str, str] = dict(person.labels)

    def increment_age(self) -> None:
        """Advance age by one month; rolls months to years at 12."""
        new_months = self.age.months + 1
        if new_months >= 12:
            self.age = dataclasses.replace(self.age, years=self.age.years + 1, months=0)
        else:
            self.age = dataclasses.replace(self.age, months=new_months)

    def is_living(self) -> bool:
        """Return True if current age is strictly less than life expectancy."""
        p = dataclasses.replace(self.person, age=self.age, labels=self.labels)
        return p.living()


class _SimulationStateUpdaterImpl(SimulationStateUpdater):
    """Internal implementation of SimulationStateUpdater.

    Immediately applies balance mutations to live AccountState objects
    and appends each transaction to the current-turn buffer.
    """

    def __init__(
        self,
        account_states: List[AccountState],
        person_states: Dict[str, _LivePersonState],
        tx_buffer: "list[Transaction]",
    ) -> None:
        self._accounts_by_id: Dict[str, AccountState] = {
            a.id: a for a in account_states
        }
        self._persons = person_states
        self._tx_buffer = tx_buffer

    def emit_transaction(self, transaction: Transaction) -> None:
        """Apply balance delta via apply_delta and record transaction in buffer.

        Supports Income (credits to_account), Expense (debits from_account),
        and Transfer (debits from_account, credits to_account). The engine
        stays type-agnostic — sign inversion for liabilities lives in
        LiabilityAccountState.apply_delta().
        """
        if isinstance(transaction, Income):
            acct = self._accounts_by_id.get(transaction.to_account)
            if acct is not None:
                acct.apply_delta(transaction.amount)
        elif isinstance(transaction, Expense):
            acct = self._accounts_by_id.get(transaction.from_account)
            if acct is not None:
                acct.apply_delta(-transaction.amount)
        elif isinstance(transaction, Transfer):
            src = self._accounts_by_id.get(transaction.from_account)
            dst = self._accounts_by_id.get(transaction.to_account)
            if src is not None:
                src.apply_delta(-transaction.amount)
            if dst is not None:
                dst.apply_delta(transaction.amount)
        self._tx_buffer.append(transaction)

    def update_person_label(self, person_id: str, facet: str, value: str) -> None:
        """Mutate the mutable labels dict for the named person."""
        state = self._persons.get(person_id)
        if state is not None:
            state.labels[facet] = value


class _SimulationLoggerImpl(SimulationLogger):
    """Internal implementation of SimulationLogger.

    Dispatches every log call to each registered LogListener in registration
    order.  If a listener raises, the exception propagates immediately — no
    swallowing.  An empty listeners list makes every call a no-op.

    Message accumulation and Python-logging delegation are the responsibility
    of the registered listeners (e.g. ListLogListener, PythonLoggingListener).
    """

    def __init__(self, listeners: List[LogListener]) -> None:
        """Initialise the logger with the given list of listeners.

        Args:
            listeners: LogListener instances to receive dispatched log calls,
                in registration order.
        """
        self._listeners = list(listeners)

    def debug(self, msg: str) -> None:
        """Dispatch a debug-level message to all registered listeners.

        Args:
            msg: The message to dispatch.
        """
        for listener in self._listeners:
            listener.debug(msg)

    def info(self, msg: str) -> None:
        """Dispatch an info-level message to all registered listeners.

        Args:
            msg: The message to dispatch.
        """
        for listener in self._listeners:
            listener.info(msg)

    def warning(self, msg: str) -> None:
        """Dispatch a warning-level message to all registered listeners.

        Args:
            msg: The message to dispatch.
        """
        for listener in self._listeners:
            listener.warning(msg)

    def error(self, msg: str) -> None:
        """Dispatch an error-level message to all registered listeners.

        Args:
            msg: The message to dispatch.
        """
        for listener in self._listeners:
            listener.error(msg)
