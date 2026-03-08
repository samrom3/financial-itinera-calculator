"""Internal engine state implementations.

These classes are private implementation details of the engine and are not
exported from the fitinera public API. They implement the Protocol interfaces
defined in interfaces.py and are wired up by SimulationEngine.run().
"""

import dataclasses
import logging
from typing import Any, Dict, List, Optional

from ..models import AccountState, Date, Person, Transaction, TurnDuration
from ..models.transaction import Expense, Income, Transfer
from .interfaces import SimulationLogger, SimulationStateUpdater, SimulationStateView

_logger = logging.getLogger("fitinera.engine")


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
        logger_ref: "list[SimulationLogger]",
    ) -> None:
        self._accounts = account_states
        self._persons = person_states
        self._metrics = metric_generators
        self._start_date = start_date
        self._current_date_ref = current_date_ref
        self._turns_completed_ref = turns_completed_ref
        self._tx_buffer = tx_buffer
        self._logger_ref = logger_ref

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
        return generator.evaluate(self, self._logger_ref[0])

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
        """Apply balance delta immediately and record transaction in buffer.

        Supports Income (adds to to_account), Expense (subtracts from from_account),
        and Transfer (subtracts from from_account, adds to to_account).
        """
        if isinstance(transaction, Income):
            acct = self._accounts_by_id.get(transaction.to_account)
            if acct is not None:
                acct.balance += transaction.amount
        elif isinstance(transaction, Expense):
            acct = self._accounts_by_id.get(transaction.from_account)
            if acct is not None:
                acct.balance -= transaction.amount
        elif isinstance(transaction, Transfer):
            src = self._accounts_by_id.get(transaction.from_account)
            dst = self._accounts_by_id.get(transaction.to_account)
            if src is not None:
                src.balance -= transaction.amount
            if dst is not None:
                dst.balance += transaction.amount
        self._tx_buffer.append(transaction)

    def update_person_label(self, person_id: str, facet: str, value: str) -> None:
        """Mutate the mutable labels dict for the named person."""
        state = self._persons.get(person_id)
        if state is not None:
            state.labels[facet] = value


class _SimulationLoggerImpl(SimulationLogger):
    """Internal implementation of SimulationLogger.

    Accumulates all messages in a list for post-run inspection via
    SimulationResult.log_messages. Also delegates to the 'fitinera.engine'
    Python logger for operator visibility. An error() call sets an internal
    flag so the engine can detect halt conditions.
    """

    def __init__(self) -> None:
        self._messages: List[str] = []
        self._has_error: bool = False

    @property
    def has_error(self) -> bool:
        """True if error() has been called at least once."""
        return self._has_error

    @property
    def error_message(self) -> Optional[str]:
        """The message from the first error() call, or None."""
        for m in self._messages:
            if m.startswith("[ERROR] "):
                return m[len("[ERROR] ") :]
        return None

    @property
    def messages(self) -> List[str]:
        """All accumulated log messages from this logger instance."""
        return list(self._messages)

    def debug(self, msg: str) -> None:
        """Log a debug-level message to fitinera.engine."""
        self._messages.append(f"[DEBUG] {msg}")
        _logger.debug(msg)

    def info(self, msg: str) -> None:
        """Log an info-level message to fitinera.engine."""
        self._messages.append(f"[INFO] {msg}")
        _logger.info(msg)

    def warning(self, msg: str) -> None:
        """Log a warning-level message to fitinera.engine."""
        self._messages.append(f"[WARNING] {msg}")
        _logger.warning(msg)

    def error(self, msg: str) -> None:
        """Log an error-level message and set the internal error flag."""
        self._messages.append(f"[ERROR] {msg}")
        _logger.error(msg)
        if not self._has_error:
            self._has_error = True
