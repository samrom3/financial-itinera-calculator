from .interfaces import MetricGenerator
from ..engine.interfaces import SimulationStateView


class NetWorthGenerator(MetricGenerator):
    """Calculates global net worth as total ASSET balances minus total LIABILITY balances."""

    def evaluate(self, view: SimulationStateView) -> float:
        raise NotImplementedError("Pending implementation")
