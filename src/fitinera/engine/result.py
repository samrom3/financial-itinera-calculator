from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from ..models.scenario import Turn


@dataclass(frozen=True)
class SimulationResult:
    """The immutable outcome of a completed simulation run.

    Attributes:
        turns: An ordered list of per-turn snapshots produced by the engine.
    """

    turns: List[Turn] = field(default_factory=list)
