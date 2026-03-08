"""Condition protocol and standard implementations for the fitinera engine.

A ``Condition`` is a predicate evaluated against a ``SimulationStateView``
at the time a Flow is about to execute. Standard implementations apply
comparison operators against simulation state and return a boolean result.
Missing entities (person not found, account not found, metric not found)
result in ``False`` without raising an exception (FR-013).
"""

import operator as _op
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Protocol

from ..models.primitives import Age

if TYPE_CHECKING:
    from ..engine.interfaces import SimulationStateView

# Mapping from ComparisonOperator to a two-argument callable.
_OPERATOR_MAP = {
    "eq": _op.eq,
    "lt": _op.lt,
    "le": _op.le,
    "gt": _op.gt,
    "ge": _op.ge,
    "ne": _op.ne,
}


def _apply_operator(operator: "ComparisonOperator", left, right) -> bool:
    """Apply *operator* to *left* and *right* and return the boolean result.

    Args:
        operator: The comparison operator to apply.
        left: The left-hand operand.
        right: The right-hand operand.

    Returns:
        Boolean result of the comparison.
    """
    fn = _OPERATOR_MAP[operator.value]
    return bool(fn(left, right))


class ComparisonOperator(Enum):
    """Enumeration of binary comparison operators used by Condition classes."""

    EQ = "eq"
    LT = "lt"
    LE = "le"
    GT = "gt"
    GE = "ge"
    NE = "ne"


class Condition(Protocol):
    """Predicate evaluated against the current simulation state.

    Implementing classes must provide an ``evaluate`` method that inspects
    the ``SimulationStateView`` and returns a boolean result.
    """

    def evaluate(self, view: "SimulationStateView") -> bool:
        """Evaluate the condition against the current simulation state.

        Args:
            view: Read-only view of the current simulation state.

        Returns:
            True if the condition is satisfied, False otherwise.
        """
        ...


@dataclass
class MetricCondition:
    """Compares a named simulation metric against a threshold value.

    Args:
        metric_name: The name of the metric to inspect via the view.
        operator: The comparison operator to apply.
        value: The threshold value to compare against.
    """

    metric_name: str
    operator: ComparisonOperator
    value: float

    def evaluate(self, view: "SimulationStateView") -> bool:
        """Evaluate the metric condition against the current simulation state.

        Calls ``view.get_metric(metric_name)`` and applies ``operator`` against
        ``value``. Returns ``False`` if the metric is not found (i.e. the view
        returns ``None``).

        Args:
            view: Read-only view of the current simulation state.

        Returns:
            True if the condition is satisfied, False otherwise.
        """
        metric_value = view.get_metric(self.metric_name)
        if metric_value is None:
            return False
        return _apply_operator(self.operator, metric_value, self.value)


@dataclass
class AccountBalanceIs:
    """Compares an account's balance against a threshold value.

    Args:
        account_id: The identifier of the account to inspect.
        operator: The comparison operator to apply.
        value: The threshold value to compare against.
    """

    account_id: str
    operator: ComparisonOperator
    value: float

    def evaluate(self, view: "SimulationStateView") -> bool:
        """Evaluate the account balance condition against the current simulation state.

        Finds the matching ``AccountState`` in ``view.get_accounts()`` and applies
        ``operator`` against ``value``. Returns ``False`` if no account with the
        given ``account_id`` is found.

        Args:
            view: Read-only view of the current simulation state.

        Returns:
            True if the condition is satisfied, False otherwise.
        """
        for account in view.get_accounts():
            if account.id == self.account_id:
                return _apply_operator(self.operator, account.balance, self.value)
        return False


@dataclass
class PersonLabelIs:
    """Checks whether a person's label facet matches a given value.

    Args:
        person_id: The identifier of the person to inspect.
        facet: The label facet to check.
        value: The expected label value.
    """

    person_id: str
    facet: str
    value: str

    def evaluate(self, view: "SimulationStateView") -> bool:
        """Evaluate the person-label condition against the current simulation state.

        Calls ``view.get_person(person_id).get_label(facet)`` and compares to
        ``value``. Returns ``False`` if the person is not found or the label
        facet is absent.

        Args:
            view: Read-only view of the current simulation state.

        Returns:
            True if the condition is satisfied, False otherwise.
        """
        person = view.get_person(self.person_id)
        if person is None:
            return False
        label_value = person.get_label(self.facet)
        if label_value is None:
            return False
        return label_value == self.value


def _age_to_tuple(age: Age) -> tuple:
    """Convert an Age to a comparable (years, months) tuple.

    Args:
        age: The Age instance to convert.

    Returns:
        A (years, months) tuple suitable for ordered comparison.
    """
    return (age.years, age.months)


@dataclass
class PersonAgeIs:
    """Compares a person's current age against a threshold.

    Args:
        person_id: The identifier of the person to inspect.
        operator: The comparison operator to apply.
        age: The threshold age to compare against.
    """

    person_id: str
    operator: ComparisonOperator
    age: Age

    def evaluate(self, view: "SimulationStateView") -> bool:
        """Evaluate the person-age condition against the current simulation state.

        Calls ``view.get_person(person_id).age`` and applies ``operator`` against
        ``age``. The comparison is performed lexicographically on
        ``(years, months)`` to handle sub-year precision. Returns ``False`` if
        the person is not found.

        Args:
            view: Read-only view of the current simulation state.

        Returns:
            True if the condition is satisfied, False otherwise.
        """
        person = view.get_person(self.person_id)
        if person is None:
            return False
        return _apply_operator(
            self.operator,
            _age_to_tuple(person.age),
            _age_to_tuple(self.age),
        )


@dataclass
class ConditionOr:
    """Logical OR of two conditions: satisfied if either child is satisfied.

    Evaluation is short-circuit: if ``left`` evaluates to ``True``, ``right``
    is not evaluated (FR-013a).

    Args:
        left: The first child condition.
        right: The second child condition.
    """

    left: Condition
    right: Condition

    def evaluate(self, view: "SimulationStateView") -> bool:
        """Evaluate the OR condition against the current simulation state.

        Short-circuits on the left operand: if ``left`` is ``True``, ``right``
        is not evaluated.

        Args:
            view: Read-only view of the current simulation state.

        Returns:
            True if at least one child condition is satisfied, False otherwise.
        """
        if self.left.evaluate(view):
            return True
        return self.right.evaluate(view)


@dataclass
class ConditionAnd:
    """Logical AND of two conditions: satisfied only if both children are satisfied.

    Evaluation is short-circuit: if ``left`` evaluates to ``False``, ``right``
    is not evaluated (FR-013a).

    Args:
        left: The first child condition.
        right: The second child condition.
    """

    left: Condition
    right: Condition

    def evaluate(self, view: "SimulationStateView") -> bool:
        """Evaluate the AND condition against the current simulation state.

        Short-circuits on the left operand: if ``left`` is ``False``, ``right``
        is not evaluated.

        Args:
            view: Read-only view of the current simulation state.

        Returns:
            True if both child conditions are satisfied, False otherwise.
        """
        if not self.left.evaluate(view):
            return False
        return self.right.evaluate(view)
