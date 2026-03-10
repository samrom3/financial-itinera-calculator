from dataclasses import dataclass, field
from typing import List, Dict
from ..models import Date, TurnDuration
from ..flows.interfaces import Flow, MetricGenerator
from .interfaces import LogListener
from .listeners import PythonLoggingListener


@dataclass(frozen=True)
class EngineConfiguration:
    """Defines the processing pipeline for the engine."""

    start_date: Date
    max_turns: TurnDuration
    metrics: Dict[str, MetricGenerator] = field(default_factory=dict)
    flows: List[Flow] = field(default_factory=list)
    log_listeners: List[LogListener] = field(
        default_factory=lambda: [PythonLoggingListener()]
    )
