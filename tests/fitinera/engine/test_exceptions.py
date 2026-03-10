"""Tests for the FitineraResult hierarchy.

Verifies instantiation, inheritance chain, ok()/message() behaviour, and
__str__ output.  FitineraError subclasses are NOT Python exceptions — they
inherit from FitineraResult, not Exception.
"""

from fitinera import (
    FitineraResult,
    FitineraSuccess,
    FitineraError,
    InternalError,
    InvalidArgumentError,
    NotFoundError,
    ReachedAllPersonsExpectancy,
    ReachedMaxTurns,
    SolvencyViolationError,
)


class TestFitineraResult:
    """Verifies the FitineraResult abstract base."""

    def test_fitinera_error_is_fitinera_result_subclass(self):
        """FitineraError inherits from FitineraResult."""
        assert issubclass(FitineraError, FitineraResult)

    def test_fitinera_success_is_fitinera_result_subclass(self):
        """FitineraSuccess inherits from FitineraResult."""
        assert issubclass(FitineraSuccess, FitineraResult)

    def test_fitinera_error_is_not_an_exception(self):
        """FitineraError does NOT inherit from Exception."""
        assert not issubclass(FitineraError, Exception)

    def test_fitinera_success_is_not_an_exception(self):
        """FitineraSuccess does NOT inherit from Exception."""
        assert not issubclass(FitineraSuccess, Exception)


class TestFitineraErrorBase:
    """Verifies FitineraError construction, ok(), message(), and __str__."""

    def test_fitinera_error_ok_returns_false(self):
        """FitineraError.ok() returns False."""
        err = FitineraError("something went wrong")
        assert err.ok() is False

    def test_fitinera_error_message_preserves_string(self):
        """FitineraError.message() returns the string passed at construction."""
        err = FitineraError("something went wrong")
        assert err.message() == "something went wrong"

    def test_fitinera_error_str_includes_message(self):
        """str(FitineraError) includes the message."""
        err = FitineraError("something went wrong")
        assert "something went wrong" in str(err)

    def test_fitinera_error_instance_is_fitinera_result(self):
        """A FitineraError instance passes isinstance check for FitineraResult."""
        err = FitineraError("err")
        assert isinstance(err, FitineraResult)


class TestInternalError:
    """Verifies InternalError is a FitineraError subclass."""

    def test_internal_error_is_fitinera_error_subclass(self):
        """InternalError is a subclass of FitineraError."""
        assert issubclass(InternalError, FitineraError)

    def test_internal_error_instance_is_fitinera_result(self):
        """An InternalError instance passes isinstance check for FitineraResult."""
        err = InternalError("invariant violated")
        assert isinstance(err, FitineraResult)

    def test_internal_error_ok_returns_false(self):
        """InternalError.ok() returns False."""
        err = InternalError("invariant violated")
        assert err.ok() is False

    def test_internal_error_message_preserves_string(self):
        """InternalError.message() returns the string passed at construction."""
        err = InternalError("invariant violated")
        assert err.message() == "invariant violated"

    def test_internal_error_instance_is_fitinera_error(self):
        """An InternalError instance passes isinstance check for FitineraError."""
        err = InternalError("invariant violated")
        assert isinstance(err, FitineraError)


class TestInvalidArgumentError:
    """Verifies InvalidArgumentError is a FitineraError subclass."""

    def test_invalid_argument_error_is_fitinera_error_subclass(self):
        """InvalidArgumentError is a subclass of FitineraError."""
        assert issubclass(InvalidArgumentError, FitineraError)

    def test_invalid_argument_error_ok_returns_false(self):
        """InvalidArgumentError.ok() returns False."""
        err = InvalidArgumentError("bad argument")
        assert err.ok() is False

    def test_invalid_argument_error_message_preserves_string(self):
        """InvalidArgumentError.message() returns the string passed at construction."""
        err = InvalidArgumentError("bad argument: x=-1")
        assert err.message() == "bad argument: x=-1"

    def test_invalid_argument_error_is_not_internal_error(self):
        """InvalidArgumentError is not a subclass of InternalError."""
        assert not issubclass(InvalidArgumentError, InternalError)


class TestNotFoundError:
    """Verifies NotFoundError is a FitineraError subclass."""

    def test_not_found_error_is_fitinera_error_subclass(self):
        """NotFoundError is a subclass of FitineraError."""
        assert issubclass(NotFoundError, FitineraError)

    def test_not_found_error_ok_returns_false(self):
        """NotFoundError.ok() returns False."""
        err = NotFoundError("account not found")
        assert err.ok() is False

    def test_not_found_error_message_preserves_string(self):
        """NotFoundError.message() returns the string passed at construction."""
        err = NotFoundError("account 'savings' not found")
        assert err.message() == "account 'savings' not found"

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

    def test_solvency_violation_error_ok_returns_false(self):
        """SolvencyViolationError.ok() returns False."""
        err = SolvencyViolationError("account 'checking' balance is -500")
        assert err.ok() is False

    def test_solvency_violation_error_instance_is_internal_error(self):
        """A SolvencyViolationError instance passes isinstance check for InternalError."""
        err = SolvencyViolationError("account 'checking' balance is -500")
        assert isinstance(err, InternalError)

    def test_solvency_violation_error_instance_is_fitinera_error(self):
        """A SolvencyViolationError instance passes isinstance check for FitineraError."""
        err = SolvencyViolationError("account 'checking' balance is -500")
        assert isinstance(err, FitineraError)

    def test_solvency_violation_error_message_preserves_string(self):
        """SolvencyViolationError.message() returns the string passed at construction."""
        msg = "account 'checking' balance is -500.00"
        err = SolvencyViolationError(msg)
        assert err.message() == msg


class TestFitineraSuccessVariants:
    """Verifies FitineraSuccess variants: ReachedAllPersonsExpectancy and ReachedMaxTurns."""

    def test_reached_all_persons_expectancy_ok_returns_true(self):
        """ReachedAllPersonsExpectancy.ok() returns True."""
        result = ReachedAllPersonsExpectancy()
        assert result.ok() is True

    def test_reached_all_persons_expectancy_is_fitinera_success(self):
        """ReachedAllPersonsExpectancy is a FitineraSuccess subclass."""
        assert issubclass(ReachedAllPersonsExpectancy, FitineraSuccess)

    def test_reached_all_persons_expectancy_is_fitinera_result(self):
        """ReachedAllPersonsExpectancy is a FitineraResult subclass."""
        assert issubclass(ReachedAllPersonsExpectancy, FitineraResult)

    def test_reached_all_persons_expectancy_message_is_non_empty(self):
        """ReachedAllPersonsExpectancy.message() returns a non-empty string."""
        result = ReachedAllPersonsExpectancy()
        assert len(result.message()) > 0

    def test_reached_max_turns_ok_returns_true(self):
        """ReachedMaxTurns.ok() returns True."""
        result = ReachedMaxTurns()
        assert result.ok() is True

    def test_reached_max_turns_is_fitinera_success(self):
        """ReachedMaxTurns is a FitineraSuccess subclass."""
        assert issubclass(ReachedMaxTurns, FitineraSuccess)

    def test_reached_max_turns_message_is_non_empty(self):
        """ReachedMaxTurns.message() returns a non-empty string."""
        result = ReachedMaxTurns()
        assert len(result.message()) > 0

    def test_str_includes_class_name_and_message(self):
        """str() of a FitineraResult includes the class name and message."""
        result = ReachedMaxTurns()
        s = str(result)
        assert "ReachedMaxTurns" in s
        assert result.message() in s
