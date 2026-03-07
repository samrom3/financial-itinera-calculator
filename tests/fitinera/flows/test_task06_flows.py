"""Tests for task-06 new and renamed Flow classes.

Covers API shapes for:
  - PersonRetirementLabelFlow (renamed from RetirementCheckFlow)
  - ConditionalLabelFlow (new in lifecycle.py)
  - AccountSolvencyGuardFlow (moved to risk.py with new signature)
  - MinSavingsStrategy Protocol (investments.py)
  - CurrentTurnExpenseStrategy (investments.py)
  - RollingAverageExpenseStrategy (investments.py)
  - AccountInterestFlow (investments.py)
  - RebalanceExtraSavingsFlow (investments.py)
  - LivingExpenseFlow with annual_inflation_rate parameter (spending.py)

TDD cycle: tests written first (red), then implementation (green).
"""

import pytest

from fitinera.flows.lifecycle import PersonRetirementLabelFlow, ConditionalLabelFlow
from fitinera.flows.risk import AccountSolvencyGuardFlow
from fitinera.flows.investments import (
    CurrentTurnExpenseStrategy,
    RollingAverageExpenseStrategy,
    AccountInterestFlow,
    RebalanceExtraSavingsFlow,
)
from fitinera.flows.spending import LivingExpenseFlow
from fitinera.flows.conditions import MetricCondition, ComparisonOperator


# ---------------------------------------------------------------------------
# PersonRetirementLabelFlow
# ---------------------------------------------------------------------------


class TestPersonRetirementLabelFlow:
    """Tests for PersonRetirementLabelFlow API shape."""

    def test_constructor_stores_person_ids(self):
        """PersonRetirementLabelFlow stores person_ids passed to constructor.

        Given person_ids ['alice', 'bob'] and a condition, the flow must
        expose them on the instance.
        """
        condition = MetricCondition("net_worth", ComparisonOperator.GE, 1_000_000.0)
        flow = PersonRetirementLabelFlow(["alice", "bob"], condition)
        assert flow.person_ids == ["alice", "bob"]

    def test_constructor_stores_condition(self):
        """PersonRetirementLabelFlow stores the condition passed to constructor.

        The condition instance must be accessible as flow.condition after
        construction.
        """
        condition = MetricCondition("net_worth", ComparisonOperator.GE, 1_000_000.0)
        flow = PersonRetirementLabelFlow(["alice"], condition)
        assert flow.condition is condition

    def test_constructor_default_status_facet(self):
        """PersonRetirementLabelFlow defaults status_facet to 'Status'.

        When not provided, status_facet must equal 'Status'.
        """
        condition = MetricCondition("net_worth", ComparisonOperator.GE, 0.0)
        flow = PersonRetirementLabelFlow(["alice"], condition)
        assert flow.status_facet == "Status"

    def test_constructor_default_retired_value(self):
        """PersonRetirementLabelFlow defaults retired_value to 'Retired'.

        When not provided, retired_value must equal 'Retired'.
        """
        condition = MetricCondition("net_worth", ComparisonOperator.GE, 0.0)
        flow = PersonRetirementLabelFlow(["alice"], condition)
        assert flow.retired_value == "Retired"

    def test_constructor_custom_status_facet_and_retired_value(self):
        """PersonRetirementLabelFlow accepts custom status_facet and retired_value.

        Providing non-default values must be reflected on the instance.
        """
        condition = MetricCondition("net_worth", ComparisonOperator.GE, 0.0)
        flow = PersonRetirementLabelFlow(
            ["alice"],
            condition,
            status_facet="LifeStage",
            retired_value="FIRE",
        )
        assert flow.status_facet == "LifeStage"
        assert flow.retired_value == "FIRE"

    def test_execute_flow_raises_not_implemented(self):
        """PersonRetirementLabelFlow.executeFlow raises NotImplementedError.

        The stub must raise NotImplementedError until real logic is added.
        """
        from unittest.mock import MagicMock

        condition = MetricCondition("net_worth", ComparisonOperator.GE, 0.0)
        flow = PersonRetirementLabelFlow(["alice"], condition)
        with pytest.raises(NotImplementedError):
            flow.executeFlow(MagicMock(), MagicMock(), MagicMock())


# ---------------------------------------------------------------------------
# ConditionalLabelFlow
# ---------------------------------------------------------------------------


class TestConditionalLabelFlow:
    """Tests for ConditionalLabelFlow API shape."""

    def test_constructor_stores_condition(self):
        """ConditionalLabelFlow stores the condition passed to constructor.

        The condition instance must be accessible as flow.condition.
        """
        condition = MetricCondition("score", ComparisonOperator.GT, 50.0)
        flow = ConditionalLabelFlow(condition, "alice", "Status", "Active")
        assert flow.condition is condition

    def test_constructor_stores_person_id(self):
        """ConditionalLabelFlow stores person_id passed to constructor.

        The person_id must be accessible on the instance.
        """
        condition = MetricCondition("score", ComparisonOperator.GT, 50.0)
        flow = ConditionalLabelFlow(condition, "alice", "Status", "Active")
        assert flow.person_id == "alice"

    def test_constructor_stores_facet(self):
        """ConditionalLabelFlow stores facet passed to constructor.

        The facet must be accessible on the instance.
        """
        condition = MetricCondition("score", ComparisonOperator.GT, 50.0)
        flow = ConditionalLabelFlow(condition, "alice", "Status", "Active")
        assert flow.facet == "Status"

    def test_constructor_stores_value(self):
        """ConditionalLabelFlow stores value passed to constructor.

        The value must be accessible on the instance.
        """
        condition = MetricCondition("score", ComparisonOperator.GT, 50.0)
        flow = ConditionalLabelFlow(condition, "alice", "Status", "Active")
        assert flow.value == "Active"

    def test_execute_flow_raises_not_implemented(self):
        """ConditionalLabelFlow.executeFlow raises NotImplementedError.

        The stub must raise NotImplementedError until real logic is added.
        """
        from unittest.mock import MagicMock

        condition = MetricCondition("score", ComparisonOperator.GT, 50.0)
        flow = ConditionalLabelFlow(condition, "alice", "Status", "Active")
        with pytest.raises(NotImplementedError):
            flow.executeFlow(MagicMock(), MagicMock(), MagicMock())


# ---------------------------------------------------------------------------
# AccountSolvencyGuardFlow (risk.py — new constructor signature)
# ---------------------------------------------------------------------------


class TestAccountSolvencyGuardFlowRisk:
    """Tests for AccountSolvencyGuardFlow in risk.py with new signature."""

    def test_constructor_default_asset_label_facet(self):
        """AccountSolvencyGuardFlow defaults asset_label_facet to 'Type'.

        When constructed with no arguments, asset_label_facet must be 'Type'.
        """
        flow = AccountSolvencyGuardFlow()
        assert flow.asset_label_facet == "Type"

    def test_constructor_default_asset_label_value(self):
        """AccountSolvencyGuardFlow defaults asset_label_value to 'ASSET'.

        When constructed with no arguments, asset_label_value must be 'ASSET'.
        """
        flow = AccountSolvencyGuardFlow()
        assert flow.asset_label_value == "ASSET"

    def test_constructor_custom_asset_label_facet(self):
        """AccountSolvencyGuardFlow accepts a custom asset_label_facet.

        Providing a custom facet must be reflected on the instance.
        """
        flow = AccountSolvencyGuardFlow(asset_label_facet="Category")
        assert flow.asset_label_facet == "Category"

    def test_constructor_custom_asset_label_value(self):
        """AccountSolvencyGuardFlow accepts a custom asset_label_value.

        Providing a custom value must be reflected on the instance.
        """
        flow = AccountSolvencyGuardFlow(asset_label_value="CHECKING")
        assert flow.asset_label_value == "CHECKING"

    def test_execute_flow_raises_not_implemented(self):
        """AccountSolvencyGuardFlow.executeFlow raises NotImplementedError.

        The stub must raise NotImplementedError until real logic is added.
        """
        from unittest.mock import MagicMock

        flow = AccountSolvencyGuardFlow()
        with pytest.raises(NotImplementedError):
            flow.executeFlow(MagicMock(), MagicMock(), MagicMock())


# ---------------------------------------------------------------------------
# CurrentTurnExpenseStrategy
# ---------------------------------------------------------------------------


class TestCurrentTurnExpenseStrategy:
    """Tests for CurrentTurnExpenseStrategy API shape."""

    def test_constructor_default_expense_multiplier(self):
        """CurrentTurnExpenseStrategy defaults expense_multiplier to 3.0.

        When constructed with no arguments, expense_multiplier must be 3.0.
        """
        strategy = CurrentTurnExpenseStrategy()
        assert strategy.expense_multiplier == 3.0

    def test_constructor_custom_expense_multiplier(self):
        """CurrentTurnExpenseStrategy accepts a custom expense_multiplier.

        Providing a custom multiplier must be reflected on the instance.
        """
        strategy = CurrentTurnExpenseStrategy(expense_multiplier=6.0)
        assert strategy.expense_multiplier == 6.0

    def test_compute_minimum_raises_not_implemented(self):
        """CurrentTurnExpenseStrategy.compute_minimum raises NotImplementedError.

        The stub must raise NotImplementedError until real logic is added.
        """
        from unittest.mock import MagicMock

        strategy = CurrentTurnExpenseStrategy()
        with pytest.raises(NotImplementedError):
            strategy.compute_minimum(MagicMock(), "checking")


# ---------------------------------------------------------------------------
# RollingAverageExpenseStrategy
# ---------------------------------------------------------------------------


class TestRollingAverageExpenseStrategy:
    """Tests for RollingAverageExpenseStrategy API shape."""

    def test_constructor_stores_lookback_months(self):
        """RollingAverageExpenseStrategy stores lookback_months.

        The lookback_months value must be accessible on the instance.
        """
        strategy = RollingAverageExpenseStrategy(lookback_months=12)
        assert strategy.lookback_months == 12

    def test_constructor_default_expense_multiplier(self):
        """RollingAverageExpenseStrategy defaults expense_multiplier to 3.0.

        When constructed with only lookback_months, expense_multiplier must be 3.0.
        """
        strategy = RollingAverageExpenseStrategy(lookback_months=6)
        assert strategy.expense_multiplier == 3.0

    def test_constructor_custom_expense_multiplier(self):
        """RollingAverageExpenseStrategy accepts a custom expense_multiplier.

        Providing a custom multiplier must be reflected on the instance.
        """
        strategy = RollingAverageExpenseStrategy(
            lookback_months=6, expense_multiplier=6.0
        )
        assert strategy.expense_multiplier == 6.0

    def test_compute_minimum_raises_not_implemented(self):
        """RollingAverageExpenseStrategy.compute_minimum raises NotImplementedError.

        The stub must raise NotImplementedError until real logic is added.
        """
        from unittest.mock import MagicMock

        strategy = RollingAverageExpenseStrategy(lookback_months=6)
        with pytest.raises(NotImplementedError):
            strategy.compute_minimum(MagicMock(), "checking")


# ---------------------------------------------------------------------------
# AccountInterestFlow
# ---------------------------------------------------------------------------


class TestAccountInterestFlow:
    """Tests for AccountInterestFlow API shape."""

    def test_constructor_stores_account_id(self):
        """AccountInterestFlow stores the account_id passed to constructor.

        The account_id must be accessible on the instance.
        """
        flow = AccountInterestFlow("savings", 0.05)
        assert flow.account_id == "savings"

    def test_constructor_stores_annual_rate(self):
        """AccountInterestFlow stores the annual_rate passed to constructor.

        The annual_rate must be accessible on the instance.
        """
        flow = AccountInterestFlow("savings", 0.05)
        assert flow.annual_rate == 0.05

    def test_execute_flow_raises_not_implemented(self):
        """AccountInterestFlow.executeFlow raises NotImplementedError.

        The stub must raise NotImplementedError until real logic is added.
        """
        from unittest.mock import MagicMock

        flow = AccountInterestFlow("savings", 0.05)
        with pytest.raises(NotImplementedError):
            flow.executeFlow(MagicMock(), MagicMock(), MagicMock())


# ---------------------------------------------------------------------------
# RebalanceExtraSavingsFlow
# ---------------------------------------------------------------------------


class TestRebalanceExtraSavingsFlow:
    """Tests for RebalanceExtraSavingsFlow API shape."""

    def test_constructor_stores_from_account(self):
        """RebalanceExtraSavingsFlow stores from_account passed to constructor.

        The from_account must be accessible on the instance.
        """
        strategy = CurrentTurnExpenseStrategy()
        flow = RebalanceExtraSavingsFlow("checking", "savings", strategy)
        assert flow.from_account == "checking"

    def test_constructor_stores_to_account(self):
        """RebalanceExtraSavingsFlow stores to_account passed to constructor.

        The to_account must be accessible on the instance.
        """
        strategy = CurrentTurnExpenseStrategy()
        flow = RebalanceExtraSavingsFlow("checking", "savings", strategy)
        assert flow.to_account == "savings"

    def test_constructor_stores_strategy(self):
        """RebalanceExtraSavingsFlow stores the strategy passed to constructor.

        The strategy instance must be accessible on the instance.
        """
        strategy = CurrentTurnExpenseStrategy()
        flow = RebalanceExtraSavingsFlow("checking", "savings", strategy)
        assert flow.strategy is strategy

    def test_execute_flow_raises_not_implemented(self):
        """RebalanceExtraSavingsFlow.executeFlow raises NotImplementedError.

        The stub must raise NotImplementedError until real logic is added.
        """
        from unittest.mock import MagicMock

        strategy = CurrentTurnExpenseStrategy()
        flow = RebalanceExtraSavingsFlow("checking", "savings", strategy)
        with pytest.raises(NotImplementedError):
            flow.executeFlow(MagicMock(), MagicMock(), MagicMock())


# ---------------------------------------------------------------------------
# MinSavingsStrategy Protocol
# ---------------------------------------------------------------------------


class TestMinSavingsStrategyProtocol:
    """Tests for MinSavingsStrategy Protocol structural compliance."""

    def test_current_turn_expense_strategy_satisfies_protocol(self):
        """CurrentTurnExpenseStrategy satisfies MinSavingsStrategy Protocol.

        Any class with compute_minimum(view, from_account) -> float
        structurally satisfies MinSavingsStrategy.
        """
        # Protocol satisfaction is structural; simply verifying the attribute exists
        strategy = CurrentTurnExpenseStrategy()
        assert hasattr(strategy, "compute_minimum")

    def test_rolling_average_expense_strategy_satisfies_protocol(self):
        """RollingAverageExpenseStrategy satisfies MinSavingsStrategy Protocol.

        Any class with compute_minimum(view, from_account) -> float
        structurally satisfies MinSavingsStrategy.
        """
        strategy = RollingAverageExpenseStrategy(lookback_months=6)
        assert hasattr(strategy, "compute_minimum")


# ---------------------------------------------------------------------------
# LivingExpenseFlow — annual_inflation_rate parameter
# ---------------------------------------------------------------------------


class TestLivingExpenseFlowInflation:
    """Tests for LivingExpenseFlow with annual_inflation_rate parameter."""

    def test_constructor_default_annual_inflation_rate(self):
        """LivingExpenseFlow defaults annual_inflation_rate to 0.0.

        When constructed with only from_account and amount, the inflation rate
        must default to 0.0.
        """
        flow = LivingExpenseFlow("checking", 2000.0)
        assert flow.annual_inflation_rate == 0.0

    def test_constructor_custom_annual_inflation_rate(self):
        """LivingExpenseFlow accepts a custom annual_inflation_rate.

        Providing a custom rate must be reflected on the instance.
        """
        flow = LivingExpenseFlow("checking", 2000.0, annual_inflation_rate=0.03)
        assert flow.annual_inflation_rate == 0.03

    def test_existing_fields_still_present(self):
        """LivingExpenseFlow still stores from_account and amount.

        Adding annual_inflation_rate must not break existing fields.
        """
        flow = LivingExpenseFlow("checking", 2000.0)
        assert flow.from_account == "checking"
        assert flow.amount == 2000.0
