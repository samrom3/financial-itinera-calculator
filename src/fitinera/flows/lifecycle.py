from .interfaces import Flow
from ..engine.interfaces import (
    SimulationStateView,
    SimulationStateUpdater,
    SimulationLogger,
)


class RetirementCheckFlow(Flow):
    """Monitors a net-worth metric and transitions persons to a retired label when a threshold is reached."""

    def __init__(
        self,
        person_ids: list[str],
        metric_name: str,
        threshold: float,
        status_facet: str = "Status",
        retired_value: str = "Retired",
    ):
        self.person_ids = person_ids
        self.metric_name = metric_name
        self.threshold = threshold
        self.status_facet = status_facet
        self.retired_value = retired_value

    def executeFlow(
        self,
        view: SimulationStateView,
        updater: SimulationStateUpdater,
        logger: SimulationLogger,
    ) -> None:
        raise NotImplementedError("Pending implementation")
