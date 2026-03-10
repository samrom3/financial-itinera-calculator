from typing import Any, List, Optional, Protocol

from ..models import AccountState, Date, Person, Transaction, TurnDuration


class SimulationStateView(Protocol):
    """Read-only interface granting read access to current and historical state."""

    def get_accounts(self) -> List[AccountState]:
        raise NotImplementedError("Pending implementation")

    def get_person(self, person_id: str) -> Optional[Person]:
        raise NotImplementedError("Pending implementation")

    def get_metric(self, name: str) -> Any:
        raise NotImplementedError("Pending implementation")

    def get_start_date(self) -> Date:
        raise NotImplementedError("Pending implementation")

    def get_current_date(self) -> Date:
        raise NotImplementedError("Pending implementation")

    def get_elapsed_duration(self) -> TurnDuration:
        raise NotImplementedError("Pending implementation")

    def get_current_turn_transactions(self) -> List[Transaction]:
        raise NotImplementedError("Pending implementation")


class SimulationStateUpdater(Protocol):
    """Controlled write access interface to emit transactions and labels."""

    def emit_transaction(self, transaction: Transaction) -> None:
        raise NotImplementedError("Pending implementation")

    def update_person_label(self, person_id: str, facet: str, value: str) -> None:
        raise NotImplementedError("Pending implementation")


class SimulationLogger(Protocol):
    """Interface for debugging info, warnings, and errors."""

    def debug(self, msg: str) -> None: ...
    def info(self, msg: str) -> None: ...
    def warning(self, msg: str) -> None: ...
    def error(self, msg: str) -> None: ...


class LogListener(Protocol):
    """Protocol for objects that receive log messages from the simulation engine.

    Implementations must be fast, synchronous, and deterministic.  If a
    LogListener raises during a dispatch call, the exception propagates
    immediately and halts the engine — listeners must not swallow errors
    silently.

    Built-in implementations:
        - PythonLoggingListener: delegates to ``logging.getLogger("fitinera.engine")``
        - ListLogListener: accumulates ``[LEVEL] msg`` strings in ``self.messages``
    """

    def debug(self, msg: str) -> None: ...
    def info(self, msg: str) -> None: ...
    def warning(self, msg: str) -> None: ...
    def error(self, msg: str) -> None: ...
