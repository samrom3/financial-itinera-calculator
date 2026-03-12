"""Tests for Condition protocol and standard implementations.

All tests are DAMP-style: each test is self-contained and explicit about
the objects it constructs. Google-style docstrings are used throughout.
"""

from unittest.mock import MagicMock

from fitinera import (
    Age,
    AccountBalanceIs,
    AssetAccountState,
    ComparisonOperator,
    Condition,
    ConditionAnd,
    ConditionOr,
    MetricCondition,
    PersonAgeIs,
    PersonLabelIs,
    SimulationStateView,
)
from fitinera.models.person import Person


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


class TestMetricConditionEvaluate:
    """Verify MetricCondition.evaluate() logic."""

    def test_evaluate_true_when_metric_ge_threshold(self):
        """evaluate() returns True when the metric satisfies the GE condition."""
        cond = MetricCondition(
            metric_name="net_worth",
            operator=ComparisonOperator.GE,
            value=1_000.0,
        )
        view = MagicMock(spec=SimulationStateView)
        view.get_metric.return_value = 2_000.0
        assert cond.evaluate(view) is True

    def test_evaluate_false_when_metric_lt_threshold(self):
        """evaluate() returns False when the metric does not satisfy the GE condition."""
        cond = MetricCondition(
            metric_name="net_worth",
            operator=ComparisonOperator.GE,
            value=1_000.0,
        )
        view = MagicMock(spec=SimulationStateView)
        view.get_metric.return_value = 500.0
        assert cond.evaluate(view) is False

    def test_evaluate_returns_false_when_metric_not_found(self):
        """evaluate() returns False when get_metric() returns None."""
        cond = MetricCondition(
            metric_name="missing_metric",
            operator=ComparisonOperator.EQ,
            value=42.0,
        )
        view = MagicMock(spec=SimulationStateView)
        view.get_metric.return_value = None
        assert cond.evaluate(view) is False

    def test_evaluate_calls_get_metric_with_correct_name(self):
        """evaluate() calls view.get_metric() with the configured metric_name."""
        cond = MetricCondition(
            metric_name="inflation_rate",
            operator=ComparisonOperator.LT,
            value=0.05,
        )
        view = MagicMock(spec=SimulationStateView)
        view.get_metric.return_value = 0.03
        cond.evaluate(view)
        view.get_metric.assert_called_once_with("inflation_rate")

    def test_evaluate_eq_operator_true(self):
        """evaluate() returns True for EQ when metric equals threshold exactly."""
        cond = MetricCondition(
            metric_name="rate",
            operator=ComparisonOperator.EQ,
            value=5.0,
        )
        view = MagicMock(spec=SimulationStateView)
        view.get_metric.return_value = 5.0
        assert cond.evaluate(view) is True

    def test_evaluate_ne_operator_true(self):
        """evaluate() returns True for NE when metric does not equal threshold."""
        cond = MetricCondition(
            metric_name="rate",
            operator=ComparisonOperator.NE,
            value=5.0,
        )
        view = MagicMock(spec=SimulationStateView)
        view.get_metric.return_value = 3.0
        assert cond.evaluate(view) is True

    def test_evaluate_le_operator_true_on_equality(self):
        """evaluate() returns True for LE when metric equals threshold."""
        cond = MetricCondition(
            metric_name="score",
            operator=ComparisonOperator.LE,
            value=100.0,
        )
        view = MagicMock(spec=SimulationStateView)
        view.get_metric.return_value = 100.0
        assert cond.evaluate(view) is True

    def test_evaluate_gt_operator_false_on_equality(self):
        """evaluate() returns False for GT when metric equals threshold."""
        cond = MetricCondition(
            metric_name="score",
            operator=ComparisonOperator.GT,
            value=100.0,
        )
        view = MagicMock(spec=SimulationStateView)
        view.get_metric.return_value = 100.0
        assert cond.evaluate(view) is False


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


class TestAccountBalanceIsEvaluate:
    """Verify AccountBalanceIs.evaluate() logic."""

    def test_evaluate_true_when_balance_gt_threshold(self):
        """evaluate() returns True when the account balance satisfies GT."""
        cond = AccountBalanceIs(
            account_id="checking",
            operator=ComparisonOperator.GT,
            value=500.0,
        )
        account = AssetAccountState(id="checking", balance=1000.0)
        view = MagicMock(spec=SimulationStateView)
        view.get_accounts.return_value = [account]
        assert cond.evaluate(view) is True

    def test_evaluate_false_when_balance_le_threshold(self):
        """evaluate() returns False when the account balance does not satisfy GT."""
        cond = AccountBalanceIs(
            account_id="checking",
            operator=ComparisonOperator.GT,
            value=500.0,
        )
        account = AssetAccountState(id="checking", balance=400.0)
        view = MagicMock(spec=SimulationStateView)
        view.get_accounts.return_value = [account]
        assert cond.evaluate(view) is False

    def test_evaluate_returns_false_when_account_not_found(self):
        """evaluate() returns False when no account with the given id exists."""
        cond = AccountBalanceIs(
            account_id="missing_account",
            operator=ComparisonOperator.EQ,
            value=0.0,
        )
        view = MagicMock(spec=SimulationStateView)
        view.get_accounts.return_value = []
        assert cond.evaluate(view) is False

    def test_evaluate_returns_false_when_account_list_does_not_contain_id(self):
        """evaluate() returns False when the account_id is absent from the list."""
        cond = AccountBalanceIs(
            account_id="savings",
            operator=ComparisonOperator.GE,
            value=0.0,
        )
        account = AssetAccountState(id="checking", balance=1000.0)
        view = MagicMock(spec=SimulationStateView)
        view.get_accounts.return_value = [account]
        assert cond.evaluate(view) is False

    def test_evaluate_matches_correct_account_when_multiple_exist(self):
        """evaluate() matches only the account with the configured account_id."""
        cond = AccountBalanceIs(
            account_id="savings",
            operator=ComparisonOperator.GE,
            value=5000.0,
        )
        checking = AssetAccountState(id="checking", balance=100.0)
        savings = AssetAccountState(id="savings", balance=10000.0)
        view = MagicMock(spec=SimulationStateView)
        view.get_accounts.return_value = [checking, savings]
        assert cond.evaluate(view) is True


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


class TestPersonLabelIsEvaluate:
    """Verify PersonLabelIs.evaluate() logic."""

    def test_evaluate_true_when_label_matches(self):
        """evaluate() returns True when the person's label facet matches the value."""
        cond = PersonLabelIs(
            person_id="alice",
            facet="employment_status",
            value="retired",
        )
        person = Person(
            id="alice",
            age=Age(years=65),
            expectancy=Age(years=85),
            labels={"employment_status": "retired"},
        )
        view = MagicMock(spec=SimulationStateView)
        view.get_person.return_value = person
        assert cond.evaluate(view) is True

    def test_evaluate_false_when_label_does_not_match(self):
        """evaluate() returns False when the person's label facet has a different value."""
        cond = PersonLabelIs(
            person_id="alice",
            facet="employment_status",
            value="retired",
        )
        person = Person(
            id="alice",
            age=Age(years=40),
            expectancy=Age(years=85),
            labels={"employment_status": "employed"},
        )
        view = MagicMock(spec=SimulationStateView)
        view.get_person.return_value = person
        assert cond.evaluate(view) is False

    def test_evaluate_false_when_person_not_found(self):
        """evaluate() returns False when get_person() returns None."""
        cond = PersonLabelIs(
            person_id="unknown",
            facet="employment_status",
            value="retired",
        )
        view = MagicMock(spec=SimulationStateView)
        view.get_person.return_value = None
        assert cond.evaluate(view) is False

    def test_evaluate_false_when_label_facet_absent(self):
        """evaluate() returns False when the person has no label for the facet."""
        cond = PersonLabelIs(
            person_id="alice",
            facet="employment_status",
            value="retired",
        )
        person = Person(
            id="alice",
            age=Age(years=65),
            expectancy=Age(years=85),
            labels={},
        )
        view = MagicMock(spec=SimulationStateView)
        view.get_person.return_value = person
        assert cond.evaluate(view) is False

    def test_evaluate_calls_get_person_with_correct_id(self):
        """evaluate() calls view.get_person() with the configured person_id."""
        cond = PersonLabelIs(
            person_id="bob",
            facet="risk_tolerance",
            value="high",
        )
        person = Person(
            id="bob",
            age=Age(years=30),
            expectancy=Age(years=80),
            labels={"risk_tolerance": "high"},
        )
        view = MagicMock(spec=SimulationStateView)
        view.get_person.return_value = person
        cond.evaluate(view)
        view.get_person.assert_called_once_with("bob")


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


class TestPersonAgeIsEvaluate:
    """Verify PersonAgeIs.evaluate() logic."""

    def test_evaluate_true_when_age_ge_threshold(self):
        """evaluate() returns True when the person's age satisfies GE."""
        cond = PersonAgeIs(
            person_id="alice",
            operator=ComparisonOperator.GE,
            age=Age(years=65),
        )
        person = Person(
            id="alice",
            age=Age(years=70),
            expectancy=Age(years=85),
        )
        view = MagicMock(spec=SimulationStateView)
        view.get_person.return_value = person
        assert cond.evaluate(view) is True

    def test_evaluate_false_when_age_lt_threshold(self):
        """evaluate() returns False when the person's age does not satisfy GE."""
        cond = PersonAgeIs(
            person_id="alice",
            operator=ComparisonOperator.GE,
            age=Age(years=65),
        )
        person = Person(
            id="alice",
            age=Age(years=40),
            expectancy=Age(years=85),
        )
        view = MagicMock(spec=SimulationStateView)
        view.get_person.return_value = person
        assert cond.evaluate(view) is False

    def test_evaluate_returns_false_when_person_not_found(self):
        """evaluate() returns False when get_person() returns None."""
        cond = PersonAgeIs(
            person_id="unknown",
            operator=ComparisonOperator.EQ,
            age=Age(years=30),
        )
        view = MagicMock(spec=SimulationStateView)
        view.get_person.return_value = None
        assert cond.evaluate(view) is False

    def test_evaluate_considers_months_in_age_comparison(self):
        """evaluate() considers months when comparing ages with the same year count."""
        cond = PersonAgeIs(
            person_id="alice",
            operator=ComparisonOperator.GT,
            age=Age(years=65, months=6),
        )
        person = Person(
            id="alice",
            age=Age(years=65, months=9),
            expectancy=Age(years=85),
        )
        view = MagicMock(spec=SimulationStateView)
        view.get_person.return_value = person
        assert cond.evaluate(view) is True

    def test_evaluate_calls_get_person_with_correct_id(self):
        """evaluate() calls view.get_person() with the configured person_id."""
        cond = PersonAgeIs(
            person_id="bob",
            operator=ComparisonOperator.LT,
            age=Age(years=67),
        )
        person = Person(
            id="bob",
            age=Age(years=50),
            expectancy=Age(years=80),
        )
        view = MagicMock(spec=SimulationStateView)
        view.get_person.return_value = person
        cond.evaluate(view)
        view.get_person.assert_called_once_with("bob")


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


class TestConditionOrEvaluate:
    """Verify ConditionOr.evaluate() logic including short-circuit behavior."""

    def test_evaluate_true_when_left_is_true(self):
        """evaluate() returns True when left evaluates to True."""
        view = MagicMock(spec=SimulationStateView)
        left = MagicMock(spec=Condition)
        left.evaluate.return_value = True
        right = MagicMock(spec=Condition)
        right.evaluate.return_value = False
        cond = ConditionOr(left=left, right=right)
        assert cond.evaluate(view) is True

    def test_evaluate_true_when_right_is_true(self):
        """evaluate() returns True when left is False but right is True."""
        view = MagicMock(spec=SimulationStateView)
        left = MagicMock(spec=Condition)
        left.evaluate.return_value = False
        right = MagicMock(spec=Condition)
        right.evaluate.return_value = True
        cond = ConditionOr(left=left, right=right)
        assert cond.evaluate(view) is True

    def test_evaluate_false_when_both_are_false(self):
        """evaluate() returns False when both left and right are False."""
        view = MagicMock(spec=SimulationStateView)
        left = MagicMock(spec=Condition)
        left.evaluate.return_value = False
        right = MagicMock(spec=Condition)
        right.evaluate.return_value = False
        cond = ConditionOr(left=left, right=right)
        assert cond.evaluate(view) is False

    def test_evaluate_true_when_both_are_true(self):
        """evaluate() returns True when both left and right are True."""
        view = MagicMock(spec=SimulationStateView)
        left = MagicMock(spec=Condition)
        left.evaluate.return_value = True
        right = MagicMock(spec=Condition)
        right.evaluate.return_value = True
        cond = ConditionOr(left=left, right=right)
        assert cond.evaluate(view) is True

    def test_evaluate_short_circuits_right_when_left_is_true(self):
        """evaluate() does not call right.evaluate() when left is True (short-circuit)."""
        view = MagicMock(spec=SimulationStateView)
        left = MagicMock(spec=Condition)
        left.evaluate.return_value = True
        right = MagicMock(spec=Condition)
        right.evaluate.return_value = False
        cond = ConditionOr(left=left, right=right)
        cond.evaluate(view)
        right.evaluate.assert_not_called()

    def test_evaluate_calls_right_when_left_is_false(self):
        """evaluate() calls right.evaluate() when left is False."""
        view = MagicMock(spec=SimulationStateView)
        left = MagicMock(spec=Condition)
        left.evaluate.return_value = False
        right = MagicMock(spec=Condition)
        right.evaluate.return_value = True
        cond = ConditionOr(left=left, right=right)
        cond.evaluate(view)
        right.evaluate.assert_called_once_with(view)


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


class TestConditionAndEvaluate:
    """Verify ConditionAnd.evaluate() logic including short-circuit behavior."""

    def test_evaluate_true_when_both_are_true(self):
        """evaluate() returns True only when both left and right are True."""
        view = MagicMock(spec=SimulationStateView)
        left = MagicMock(spec=Condition)
        left.evaluate.return_value = True
        right = MagicMock(spec=Condition)
        right.evaluate.return_value = True
        cond = ConditionAnd(left=left, right=right)
        assert cond.evaluate(view) is True

    def test_evaluate_false_when_left_is_false(self):
        """evaluate() returns False when left is False."""
        view = MagicMock(spec=SimulationStateView)
        left = MagicMock(spec=Condition)
        left.evaluate.return_value = False
        right = MagicMock(spec=Condition)
        right.evaluate.return_value = True
        cond = ConditionAnd(left=left, right=right)
        assert cond.evaluate(view) is False

    def test_evaluate_false_when_right_is_false(self):
        """evaluate() returns False when right is False."""
        view = MagicMock(spec=SimulationStateView)
        left = MagicMock(spec=Condition)
        left.evaluate.return_value = True
        right = MagicMock(spec=Condition)
        right.evaluate.return_value = False
        cond = ConditionAnd(left=left, right=right)
        assert cond.evaluate(view) is False

    def test_evaluate_false_when_both_are_false(self):
        """evaluate() returns False when both left and right are False."""
        view = MagicMock(spec=SimulationStateView)
        left = MagicMock(spec=Condition)
        left.evaluate.return_value = False
        right = MagicMock(spec=Condition)
        right.evaluate.return_value = False
        cond = ConditionAnd(left=left, right=right)
        assert cond.evaluate(view) is False

    def test_evaluate_short_circuits_right_when_left_is_false(self):
        """evaluate() does not call right.evaluate() when left is False (short-circuit)."""
        view = MagicMock(spec=SimulationStateView)
        left = MagicMock(spec=Condition)
        left.evaluate.return_value = False
        right = MagicMock(spec=Condition)
        right.evaluate.return_value = True
        cond = ConditionAnd(left=left, right=right)
        cond.evaluate(view)
        right.evaluate.assert_not_called()

    def test_evaluate_calls_right_when_left_is_true(self):
        """evaluate() calls right.evaluate() when left is True."""
        view = MagicMock(spec=SimulationStateView)
        left = MagicMock(spec=Condition)
        left.evaluate.return_value = True
        right = MagicMock(spec=Condition)
        right.evaluate.return_value = False
        cond = ConditionAnd(left=left, right=right)
        cond.evaluate(view)
        right.evaluate.assert_called_once_with(view)
