from typing import Protocol, Any, Optional, List
from ..models import Account, Person, Transaction


class SimulationStateView(Protocol):
    """Read-only interface granting read access to current and historical state."""

    def get_accounts(self) -> List[Account]:
        raise NotImplementedError("Pending implementation")

    def get_person(self, person_id: str) -> Optional[Person]:
        raise NotImplementedError("Pending implementation")

    def get_metric(self, name: str) -> Any:
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
