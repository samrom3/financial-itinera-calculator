"""Internal engine state implementations.

These classes are private implementation details of the engine and are not
exported from the fitinera public API. They implement the Protocol interfaces
defined in interfaces.py and will be fully wired up in story-10.
"""

from typing import Any, List, Optional

from ..models import AccountState, Date, ElapsedDuration, Person, Transaction
from .interfaces import SimulationLogger, SimulationStateUpdater, SimulationStateView


class _SimulationStateViewImpl(SimulationStateView):
    """Internal implementation of SimulationStateView.

    All methods raise NotImplementedError until the engine is wired in story-10.
    """

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

    def get_elapsed_duration(self) -> ElapsedDuration:
        raise NotImplementedError("Pending implementation")

    def get_current_turn_transactions(self) -> List[Transaction]:
        raise NotImplementedError("Pending implementation")


class _SimulationStateUpdaterImpl(SimulationStateUpdater):
    """Internal implementation of SimulationStateUpdater.

    All methods raise NotImplementedError until the engine is wired in story-10.
    """

    def emit_transaction(self, transaction: Transaction) -> None:
        raise NotImplementedError("Pending implementation")

    def update_person_label(self, person_id: str, facet: str, value: str) -> None:
        raise NotImplementedError("Pending implementation")


class _SimulationLoggerImpl(SimulationLogger):
    """Internal implementation of SimulationLogger.

    All methods raise NotImplementedError until the engine is wired in story-10.
    """

    def debug(self, msg: str) -> None:
        raise NotImplementedError("Pending implementation")

    def info(self, msg: str) -> None:
        raise NotImplementedError("Pending implementation")

    def warning(self, msg: str) -> None:
        raise NotImplementedError("Pending implementation")

    def error(self, msg: str) -> None:
        raise NotImplementedError("Pending implementation")
