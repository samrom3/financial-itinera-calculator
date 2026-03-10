from typing import Optional, Protocol, Any

from ..engine.interfaces import (
    SimulationStateView,
    SimulationStateUpdater,
    SimulationLogger,
)
from ..engine.result import FitineraError


class Flow(Protocol):
    """A computational component that mutates simulation state each turn.

    Returns None to signal the simulation should continue, or a FitineraError
    subclass to signal an unrecoverable halt condition.  The returned error type
    must be documented in the Flow's docstring under a ``Returns:`` section.
    """

    def executeFlow(
        self,
        view: SimulationStateView,
        updater: SimulationStateUpdater,
        logger: SimulationLogger,
    ) -> Optional[FitineraError]:
        raise NotImplementedError("Pending implementation")


class MetricGenerator(Protocol):
    """A computational logic to passively observe metrics."""

    def evaluate(self, view: SimulationStateView, logger: SimulationLogger) -> Any:
        raise NotImplementedError("Pending implementation")
