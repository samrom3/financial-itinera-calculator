from dataclasses import dataclass, field
from typing import List, Dict
from ..models import Date, TurnDuration
from ..flows.interfaces import Flow, MetricGenerator


@dataclass(frozen=True)
class EngineConfiguration:
    """Defines the processing pipeline for the engine."""

    start_date: Date
    max_turns: TurnDuration
    metrics: Dict[str, MetricGenerator] = field(default_factory=dict)
    flows: List[Flow] = field(default_factory=list)
