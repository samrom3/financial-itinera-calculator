"""Typed exception hierarchy for fitinera.

All fitinera-specific exceptions inherit from FitineraError, which in turn
inherits from the built-in Exception.  Flows signal unrecoverable,
simulation-halting conditions by raising a FitineraError subclass.

Hierarchy::

    FitineraError
    ├── InternalError          # invariant violations inside the engine
    │   └── SolvencyViolationError  # account solvency guard halts
    ├── InvalidArgumentError   # bad construction-time arguments
    └── NotFoundError          # requested entity does not exist
"""


class FitineraError(Exception):
    """Base class for all fitinera-specific exceptions.

    Flows raise a FitineraError subclass to signal an unrecoverable condition
    that must halt the simulation.  The raised type must always be documented
    in the Flow's docstring so that callers are never surprised.
    """


class InternalError(FitineraError):
    """Raised when an internal engine invariant is violated.

    Use this type (or a subclass) when the engine itself detects a
    condition that should never occur under correct usage.
    """


class InvalidArgumentError(FitineraError):
    """Raised when a construction-time argument is invalid.

    Use this type when a Flow or engine component receives an argument
    that violates its documented preconditions (e.g. a negative amount,
    an empty account ID).
    """


class NotFoundError(FitineraError):
    """Raised when a requested entity does not exist in the simulation state.

    Use this type when a lookup by ID or name fails and there is no
    sensible default to fall back on.
    """


class SolvencyViolationError(InternalError):
    """Raised by AccountSolvencyGuardFlow when an account becomes insolvent.

    The message should include the account ID and the offending balance so
    the caller can identify which account triggered the halt.

    Raises:
        SolvencyViolationError: When an account balance falls below zero.
    """
