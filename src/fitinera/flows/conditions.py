"""Condition protocol and standard implementations for the fitinera engine.

A ``Condition`` is a predicate evaluated against a ``SimulationStateView``
at the time a Flow is about to execute. Standard implementations are stubs
that raise ``NotImplementedError`` until evaluation logic is added.
"""

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Protocol

from ..models.primitives import Age

if TYPE_CHECKING:
    from ..engine.interfaces import SimulationStateView


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
        raise NotImplementedError("Pending implementation")


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

        Args:
            view: Read-only view of the current simulation state.

        Returns:
            True if the condition is satisfied, False otherwise.
        """
        raise NotImplementedError("Pending implementation")


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

        Args:
            view: Read-only view of the current simulation state.

        Returns:
            True if the condition is satisfied, False otherwise.
        """
        raise NotImplementedError("Pending implementation")


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

        Args:
            view: Read-only view of the current simulation state.

        Returns:
            True if the condition is satisfied, False otherwise.
        """
        raise NotImplementedError("Pending implementation")


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

        Args:
            view: Read-only view of the current simulation state.

        Returns:
            True if the condition is satisfied, False otherwise.
        """
        raise NotImplementedError("Pending implementation")


@dataclass
class ConditionOr:
    """Logical OR of two conditions: satisfied if either child is satisfied.

    Args:
        left: The first child condition.
        right: The second child condition.
    """

    left: Condition
    right: Condition

    def evaluate(self, view: "SimulationStateView") -> bool:
        """Evaluate the OR condition against the current simulation state.

        Args:
            view: Read-only view of the current simulation state.

        Returns:
            True if at least one child condition is satisfied, False otherwise.
        """
        raise NotImplementedError("Pending implementation")


@dataclass
class ConditionAnd:
    """Logical AND of two conditions: satisfied only if both children are satisfied.

    Args:
        left: The first child condition.
        right: The second child condition.
    """

    left: Condition
    right: Condition

    def evaluate(self, view: "SimulationStateView") -> bool:
        """Evaluate the AND condition against the current simulation state.

        Args:
            view: Read-only view of the current simulation state.

        Returns:
            True if both child conditions are satisfied, False otherwise.
        """
        raise NotImplementedError("Pending implementation")
