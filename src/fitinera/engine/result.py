"""Result types for fitinera simulations.

All fitinera halt signals and the simulation outcome type live here.

Hierarchy::

    FitineraResult          (abstract — ok(), message(), __str__)
    ├── FitineraSuccess     (abstract — ok() → True)
    │   ├── ReachedAllPersonsExpectancy
    │   └── ReachedMaxTurns
    └── FitineraError       (abstract — ok() → False)
        ├── InternalError
        │   └── SolvencyViolationError
        ├── InvalidArgumentError
        └── NotFoundError

SimulationData
    result: FitineraResult
    turns:  List[Turn]
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List

from ..models.scenario import Turn


class FitineraResult(ABC):
    """Abstract base for all fitinera simulation halt signals.

    Every normal or abnormal halt is represented as a FitineraResult instance.
    Flows return Optional[FitineraError] from executeFlow(); the engine wraps
    the final halt reason — success or error — in SimulationData.result.
    """

    @abstractmethod
    def ok(self) -> bool:
        """Return True if this result represents a successful halt."""

    @abstractmethod
    def message(self) -> str:
        """Return a human-readable description of this result."""

    def __str__(self) -> str:
        return f"{type(self).__name__}: {self.message()}"

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.message()!r})"


class FitineraSuccess(FitineraResult):
    """Base for all normal (non-error) halt conditions.

    ok() always returns True.
    """

    def ok(self) -> bool:
        return True


class ReachedAllPersonsExpectancy(FitineraSuccess):
    """All persons in the scenario have exceeded their life expectancy."""

    def message(self) -> str:
        return "Simulation complete: all persons have reached their life expectancy."


class ReachedMaxTurns(FitineraSuccess):
    """The simulation ran for the configured maximum number of turns."""

    def message(self) -> str:
        return "Simulation complete: maximum number of turns reached."


class FitineraError(FitineraResult):
    """Base for all fitinera error halt conditions.

    Flows return a FitineraError subclass from executeFlow() to signal an
    unrecoverable condition that must halt the simulation.  The returned type
    must always be documented in the Flow's docstring under a ``Returns:``
    section so callers are never surprised.  ok() always returns False.
    """

    def __init__(self, msg: str = "") -> None:
        self._msg = msg

    def ok(self) -> bool:
        return False

    def message(self) -> str:
        return self._msg


class InternalError(FitineraError):
    """An internal engine invariant was violated.

    Use this type (or a subclass) when the engine itself detects a
    condition that should never occur under correct usage.
    """


class InvalidArgumentError(FitineraError):
    """A construction-time argument is invalid.

    Use this type when a Flow or engine component receives an argument
    that violates its documented preconditions (e.g. a negative amount,
    an empty account ID).
    """


class NotFoundError(FitineraError):
    """A requested entity does not exist in the simulation state.

    Use this type when a lookup by ID or name fails and there is no
    sensible default to fall back on.
    """


class SolvencyViolationError(InternalError):
    """An asset account balance dropped below zero.

    Returned by AssetSolvencyGuardFlow when a monitored asset account
    becomes insolvent.  The message includes the account ID and offending
    balance so the caller can identify which account triggered the halt.
    """


@dataclass(frozen=True)
class SimulationData:
    """The immutable outcome of a completed simulation run.

    Attributes:
        result: The reason the simulation halted.  A FitineraSuccess subclass
            for normal completion, or a FitineraError subclass for an error halt.
            Inspect ``result.ok()`` to determine which.
        turns: An ordered list of per-turn snapshots produced by the engine up
            to and including the final completed turn.
    """

    result: FitineraResult
    turns: List[Turn] = field(default_factory=list)
