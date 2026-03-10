"""Re-exports from fitinera.engine.result.

The result type hierarchy (FitineraResult, FitineraError, etc.) lives in
``fitinera.engine.result``.  This module re-exports everything for backwards
compatibility with any code that imports directly from ``fitinera.engine.exceptions``.
"""

from .result import (  # noqa: F401
    FitineraResult,
    FitineraSuccess,
    ReachedAllPersonsExpectancy,
    ReachedMaxTurns,
    FitineraError,
    InternalError,
    InvalidArgumentError,
    NotFoundError,
    SolvencyViolationError,
)
