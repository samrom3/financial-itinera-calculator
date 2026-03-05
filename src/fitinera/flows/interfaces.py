from typing import Protocol, Any
from ..engine.interfaces import (
    SimulationStateView,
    SimulationStateUpdater,
    SimulationLogger,
)


class Flow(Protocol):
    """A computational component to mutate state."""

    def executeFlow(
        self,
        view: SimulationStateView,
        updater: SimulationStateUpdater,
        logger: SimulationLogger,
    ) -> None:
        raise NotImplementedError("Pending implementation")


class MetricGenerator(Protocol):
    """A computational logic to passively observe metrics."""

    def evaluate(self, view: SimulationStateView) -> Any:
        raise NotImplementedError("Pending implementation")
