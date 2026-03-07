"""Tests for Condition protocol and standard implementations.

All tests are DAMP-style: each test is self-contained and explicit about
the objects it constructs. Google-style docstrings are used throughout.
"""

import pytest
from unittest.mock import MagicMock

from fitinera import (
    Age,
    ComparisonOperator,
    Condition,
    MetricCondition,
    AccountBalanceIs,
    PersonLabelIs,
    PersonAgeIs,
    ConditionOr,
    ConditionAnd,
    SimulationStateView,
)


# ---------------------------------------------------------------------------
# ComparisonOperator
# ---------------------------------------------------------------------------


class TestComparisonOperatorMembers:
    """Verify that ComparisonOperator exposes the expected six members."""

    def test_eq_member_exists(self):
        """ComparisonOperator.EQ should exist."""
        assert ComparisonOperator.EQ is not None

    def test_lt_member_exists(self):
        """ComparisonOperator.LT should exist."""
        assert ComparisonOperator.LT is not None

    def test_le_member_exists(self):
        """ComparisonOperator.LE should exist."""
        assert ComparisonOperator.LE is not None

    def test_gt_member_exists(self):
        """ComparisonOperator.GT should exist."""
        assert ComparisonOperator.GT is not None

    def test_ge_member_exists(self):
        """ComparisonOperator.GE should exist."""
        assert ComparisonOperator.GE is not None

    def test_ne_member_exists(self):
        """ComparisonOperator.NE should exist."""
        assert ComparisonOperator.NE is not None


# ---------------------------------------------------------------------------
# Condition protocol — structural check
# ---------------------------------------------------------------------------


class TestConditionProtocol:
    """Verify that Condition is a Protocol with an evaluate() method."""

    def test_condition_is_importable(self):
        """Condition should be importable from fitinera."""
        assert Condition is not None

    def test_condition_has_evaluate_method(self):
        """Condition protocol should expose an evaluate method."""
        assert hasattr(Condition, "evaluate")


# ---------------------------------------------------------------------------
# MetricCondition
# ---------------------------------------------------------------------------


class TestMetricConditionShape:
    """Verify the API shape of MetricCondition."""

    def test_construction_stores_attributes(self):
        """MetricCondition should accept metric_name, operator, and value."""
        cond = MetricCondition(
            metric_name="net_worth",
            operator=ComparisonOperator.GE,
            value=1_000_000.0,
        )
        assert cond.metric_name == "net_worth"
        assert cond.operator is ComparisonOperator.GE
        assert cond.value == 1_000_000.0

    def test_evaluate_raises_not_implemented(self):
        """MetricCondition.evaluate() should raise NotImplementedError (stub)."""
        cond = MetricCondition(
            metric_name="net_worth",
            operator=ComparisonOperator.GE,
            value=1_000_000.0,
        )
        mock_view = MagicMock(spec=SimulationStateView)
        with pytest.raises(NotImplementedError):
            cond.evaluate(mock_view)


# ---------------------------------------------------------------------------
# AccountBalanceIs
# ---------------------------------------------------------------------------


class TestAccountBalanceIsShape:
    """Verify the API shape of AccountBalanceIs."""

    def test_construction_stores_attributes(self):
        """AccountBalanceIs should accept account_id, operator, and value."""
        cond = AccountBalanceIs(
            account_id="checking",
            operator=ComparisonOperator.GT,
            value=500.0,
        )
        assert cond.account_id == "checking"
        assert cond.operator is ComparisonOperator.GT
        assert cond.value == 500.0

    def test_evaluate_raises_not_implemented(self):
        """AccountBalanceIs.evaluate() should raise NotImplementedError (stub)."""
        cond = AccountBalanceIs(
            account_id="checking",
            operator=ComparisonOperator.GT,
            value=500.0,
        )
        mock_view = MagicMock(spec=SimulationStateView)
        with pytest.raises(NotImplementedError):
            cond.evaluate(mock_view)


# ---------------------------------------------------------------------------
# PersonLabelIs
# ---------------------------------------------------------------------------


class TestPersonLabelIsShape:
    """Verify the API shape of PersonLabelIs."""

    def test_construction_stores_attributes(self):
        """PersonLabelIs should accept person_id, facet, and value."""
        cond = PersonLabelIs(
            person_id="alice",
            facet="employment_status",
            value="retired",
        )
        assert cond.person_id == "alice"
        assert cond.facet == "employment_status"
        assert cond.value == "retired"

    def test_evaluate_raises_not_implemented(self):
        """PersonLabelIs.evaluate() should raise NotImplementedError (stub)."""
        cond = PersonLabelIs(
            person_id="alice",
            facet="employment_status",
            value="retired",
        )
        mock_view = MagicMock(spec=SimulationStateView)
        with pytest.raises(NotImplementedError):
            cond.evaluate(mock_view)


# ---------------------------------------------------------------------------
# PersonAgeIs
# ---------------------------------------------------------------------------


class TestPersonAgeIsShape:
    """Verify the API shape of PersonAgeIs."""

    def test_construction_stores_attributes(self):
        """PersonAgeIs should accept person_id, operator, and age."""
        age = Age(years=65)
        cond = PersonAgeIs(
            person_id="alice",
            operator=ComparisonOperator.GE,
            age=age,
        )
        assert cond.person_id == "alice"
        assert cond.operator is ComparisonOperator.GE
        assert cond.age == age

    def test_evaluate_raises_not_implemented(self):
        """PersonAgeIs.evaluate() should raise NotImplementedError (stub)."""
        age = Age(years=65)
        cond = PersonAgeIs(
            person_id="alice",
            operator=ComparisonOperator.GE,
            age=age,
        )
        mock_view = MagicMock(spec=SimulationStateView)
        with pytest.raises(NotImplementedError):
            cond.evaluate(mock_view)


# ---------------------------------------------------------------------------
# ConditionOr
# ---------------------------------------------------------------------------


class TestConditionOrShape:
    """Verify the API shape of ConditionOr."""

    def test_construction_stores_left_and_right(self):
        """ConditionOr should accept left and right Condition instances."""
        left = MetricCondition(
            metric_name="net_worth", operator=ComparisonOperator.GE, value=0.0
        )
        right = AccountBalanceIs(
            account_id="checking", operator=ComparisonOperator.GT, value=0.0
        )
        cond = ConditionOr(left=left, right=right)
        assert cond.left is left
        assert cond.right is right

    def test_evaluate_raises_not_implemented(self):
        """ConditionOr.evaluate() should raise NotImplementedError (stub)."""
        left = MetricCondition(
            metric_name="net_worth", operator=ComparisonOperator.GE, value=0.0
        )
        right = AccountBalanceIs(
            account_id="checking", operator=ComparisonOperator.GT, value=0.0
        )
        cond = ConditionOr(left=left, right=right)
        mock_view = MagicMock(spec=SimulationStateView)
        with pytest.raises(NotImplementedError):
            cond.evaluate(mock_view)


# ---------------------------------------------------------------------------
# ConditionAnd
# ---------------------------------------------------------------------------


class TestConditionAndShape:
    """Verify the API shape of ConditionAnd."""

    def test_construction_stores_left_and_right(self):
        """ConditionAnd should accept left and right Condition instances."""
        left = MetricCondition(
            metric_name="net_worth", operator=ComparisonOperator.GE, value=0.0
        )
        right = PersonLabelIs(
            person_id="alice", facet="employment_status", value="retired"
        )
        cond = ConditionAnd(left=left, right=right)
        assert cond.left is left
        assert cond.right is right

    def test_evaluate_raises_not_implemented(self):
        """ConditionAnd.evaluate() should raise NotImplementedError (stub)."""
        left = MetricCondition(
            metric_name="net_worth", operator=ComparisonOperator.GE, value=0.0
        )
        right = PersonLabelIs(
            person_id="alice", facet="employment_status", value="retired"
        )
        cond = ConditionAnd(left=left, right=right)
        mock_view = MagicMock(spec=SimulationStateView)
        with pytest.raises(NotImplementedError):
            cond.evaluate(mock_view)
