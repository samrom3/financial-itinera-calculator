"""Tests for the FitineraError exception hierarchy.

Verifies instantiation, inheritance chain, and message preservation.
No listener stubs are exercised here — this file covers exceptions only.
"""

import pytest

from fitinera import (
    FitineraError,
    InternalError,
    InvalidArgumentError,
    NotFoundError,
    SolvencyViolationError,
)


class TestFitineraErrorBase:
    """Verifies that FitineraError is a proper Exception subclass."""

    def test_fitinera_error_is_exception_subclass(self):
        """FitineraError inherits from Exception."""
        assert issubclass(FitineraError, Exception)

    def test_fitinera_error_can_be_instantiated_with_message(self):
        """FitineraError stores and exposes its message string."""
        err = FitineraError("something went wrong")
        assert str(err) == "something went wrong"

    def test_fitinera_error_can_be_raised_and_caught(self):
        """FitineraError can be raised and caught as an Exception."""
        with pytest.raises(Exception):
            raise FitineraError("base error")

    def test_fitinera_error_can_be_caught_as_itself(self):
        """FitineraError can be caught by its own type."""
        with pytest.raises(FitineraError):
            raise FitineraError("base error")


class TestInternalError:
    """Verifies InternalError is a FitineraError subclass."""

    def test_internal_error_is_fitinera_error_subclass(self):
        """InternalError is a subclass of FitineraError."""
        assert issubclass(InternalError, FitineraError)

    def test_internal_error_is_exception_subclass(self):
        """InternalError is a subclass of Exception."""
        assert issubclass(InternalError, Exception)

    def test_internal_error_instance_is_fitinera_error(self):
        """An InternalError instance passes isinstance check for FitineraError."""
        err = InternalError("invariant violated")
        assert isinstance(err, FitineraError)

    def test_internal_error_preserves_message(self):
        """InternalError stores and exposes its message string."""
        err = InternalError("invariant violated")
        assert str(err) == "invariant violated"

    def test_internal_error_can_be_raised_and_caught_as_fitinera_error(self):
        """InternalError raised can be caught as FitineraError."""
        with pytest.raises(FitineraError):
            raise InternalError("invariant violated")


class TestInvalidArgumentError:
    """Verifies InvalidArgumentError is a FitineraError subclass."""

    def test_invalid_argument_error_is_fitinera_error_subclass(self):
        """InvalidArgumentError is a subclass of FitineraError."""
        assert issubclass(InvalidArgumentError, FitineraError)

    def test_invalid_argument_error_instance_is_fitinera_error(self):
        """An InvalidArgumentError instance passes isinstance check for FitineraError."""
        err = InvalidArgumentError("bad argument")
        assert isinstance(err, FitineraError)

    def test_invalid_argument_error_preserves_message(self):
        """InvalidArgumentError stores and exposes its message string."""
        err = InvalidArgumentError("bad argument: x=-1")
        assert str(err) == "bad argument: x=-1"

    def test_invalid_argument_error_is_not_internal_error(self):
        """InvalidArgumentError is not a subclass of InternalError."""
        assert not issubclass(InvalidArgumentError, InternalError)


class TestNotFoundError:
    """Verifies NotFoundError is a FitineraError subclass."""

    def test_not_found_error_is_fitinera_error_subclass(self):
        """NotFoundError is a subclass of FitineraError."""
        assert issubclass(NotFoundError, FitineraError)

    def test_not_found_error_instance_is_fitinera_error(self):
        """A NotFoundError instance passes isinstance check for FitineraError."""
        err = NotFoundError("account not found")
        assert isinstance(err, FitineraError)

    def test_not_found_error_preserves_message(self):
        """NotFoundError stores and exposes its message string."""
        err = NotFoundError("account 'savings' not found")
        assert str(err) == "account 'savings' not found"

    def test_not_found_error_is_not_internal_error(self):
        """NotFoundError is not a subclass of InternalError."""
        assert not issubclass(NotFoundError, InternalError)


class TestSolvencyViolationError:
    """Verifies SolvencyViolationError inherits from InternalError."""

    def test_solvency_violation_error_is_internal_error_subclass(self):
        """SolvencyViolationError is a subclass of InternalError."""
        assert issubclass(SolvencyViolationError, InternalError)

    def test_solvency_violation_error_is_fitinera_error_subclass(self):
        """SolvencyViolationError is a subclass of FitineraError (via InternalError)."""
        assert issubclass(SolvencyViolationError, FitineraError)

    def test_solvency_violation_error_instance_is_internal_error(self):
        """A SolvencyViolationError instance passes isinstance check for InternalError."""
        err = SolvencyViolationError("account 'checking' balance is -500")
        assert isinstance(err, InternalError)

    def test_solvency_violation_error_instance_is_fitinera_error(self):
        """A SolvencyViolationError instance passes isinstance check for FitineraError."""
        err = SolvencyViolationError("account 'checking' balance is -500")
        assert isinstance(err, FitineraError)

    def test_solvency_violation_error_preserves_message(self):
        """SolvencyViolationError stores and exposes its message string."""
        msg = "account 'checking' balance is -500.00"
        err = SolvencyViolationError(msg)
        assert str(err) == msg

    def test_solvency_violation_error_can_be_caught_as_fitinera_error(self):
        """SolvencyViolationError raised can be caught as FitineraError."""
        with pytest.raises(FitineraError):
            raise SolvencyViolationError("insolvency detected")

    def test_solvency_violation_error_can_be_caught_as_internal_error(self):
        """SolvencyViolationError raised can be caught as InternalError."""
        with pytest.raises(InternalError):
            raise SolvencyViolationError("insolvency detected")
