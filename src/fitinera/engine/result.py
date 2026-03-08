from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from ..models.scenario import Turn


@dataclass(frozen=True)
class SimulationResult:
    """The immutable outcome of a completed simulation run.

    Attributes:
        turns: An ordered list of per-turn snapshots produced by the engine.
        success: True when the simulation ran to natural completion; False when
            a fatal error (e.g. insolvency) caused an early halt.
        error_message: Human-readable description of the failure when
            ``success`` is False; None otherwise.
        log_messages: All log messages emitted during the run, prefixed with
            their level (e.g. ``[INFO] ...``, ``[ERROR] ...``). Useful for
            post-run inspection without configuring Python logging.
    """

    turns: List[Turn] = field(default_factory=list)
    success: bool = True
    error_message: Optional[str] = None
    log_messages: List[str] = field(default_factory=list)
