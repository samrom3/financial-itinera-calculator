from .configuration import EngineConfiguration
from .result import SimulationResult
from ..models import SimulationScenario


class SimulationEngine:
    """The main controller for running a financial simulation pipeline."""

    def __init__(self, configuration: EngineConfiguration):
        self.configuration = configuration

    def run(self, scenario: SimulationScenario) -> SimulationResult:
        raise NotImplementedError("Pending implementation")
