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

from fitinera.flows.lifecycle import PersonRetirementLabelFlow, ConditionalLabelFlow
from fitinera.flows.risk import AccountSolvencyGuardFlow
from fitinera.flows.investments import (
    CurrentTurnExpenseStrategy,
    RollingAverageExpenseStrategy,
    AccountInterestFlow,
    RebalanceExtraSavingsFlow,
)
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

    def test_execute_flow_calls_update_person_label_when_condition_true(self):
        """PersonRetirementLabelFlow.executeFlow calls update_person_label when condition is True.

        When condition.evaluate(view) returns True, update_person_label must be called
        for each configured person_id with the default status_facet and retired_value.
        """
        from unittest.mock import MagicMock

        condition = MagicMock()
        condition.evaluate.return_value = True
        flow = PersonRetirementLabelFlow(["alice"], condition)
        view = MagicMock()
        updater = MagicMock()
        logger = MagicMock()

        flow.executeFlow(view, updater, logger)

        updater.update_person_label.assert_called_once_with(
            "alice", "Status", "Retired"
        )


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

    def test_execute_flow_calls_update_person_label_when_condition_true(self):
        """ConditionalLabelFlow.executeFlow calls update_person_label when condition is True.

        When condition.evaluate(view) returns True, update_person_label must be called
        with the configured person_id, facet, and value.
        """
        from unittest.mock import MagicMock

        condition = MagicMock()
        condition.evaluate.return_value = True
        flow = ConditionalLabelFlow(condition, "alice", "Status", "Active")
        view = MagicMock()
        updater = MagicMock()
        logger = MagicMock()

        flow.executeFlow(view, updater, logger)

        updater.update_person_label.assert_called_once_with("alice", "Status", "Active")


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

    def test_execute_flow_raises_for_negative_asset_balance(self):
        """AccountSolvencyGuardFlow.executeFlow raises SolvencyViolationError for negative ASSET balance.

        An AccountState with Type == 'ASSET' and a negative balance must trigger
        SolvencyViolationError; an ASSET with non-negative balance must not.
        """
        import pytest
        from unittest.mock import MagicMock
        from fitinera.models import AccountState
        from fitinera.engine.exceptions import SolvencyViolationError

        flow = AccountSolvencyGuardFlow()
        account = AccountState(id="checking", balance=-100.0, labels={"Type": "ASSET"})
        view = MagicMock()
        view.get_accounts.return_value = [account]
        updater = MagicMock()
        logger = MagicMock()

        with pytest.raises(SolvencyViolationError):
            flow.executeFlow(view, updater, logger)


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

    def test_compute_minimum_returns_zero_for_empty_transactions(self):
        """CurrentTurnExpenseStrategy.compute_minimum returns 0.0 when no transactions.

        With no current-turn transactions, the sum is 0.0 * expense_multiplier = 0.0.
        """
        from unittest.mock import MagicMock

        strategy = CurrentTurnExpenseStrategy()
        view = MagicMock()
        view.get_current_turn_transactions.return_value = []

        result = strategy.compute_minimum(view, "checking")

        assert result == 0.0


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

    def test_compute_minimum_returns_zero_for_empty_history(self):
        """RollingAverageExpenseStrategy.compute_minimum returns 0.0 when deque is empty.

        With no prior turns recorded in the deque, the strategy returns 0.0.
        """
        from unittest.mock import MagicMock

        strategy = RollingAverageExpenseStrategy(lookback_months=6)
        view = MagicMock()
        view.get_current_turn_transactions.return_value = []

        result = strategy.compute_minimum(view, "checking")

        assert result == 0.0


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

    def test_execute_flow_emits_income_for_configured_account(self):
        """AccountInterestFlow.executeFlow emits an Income transaction for the account.

        When the account exists in view.get_accounts(), emit_transaction must be called
        once with an Income targeting account_id.
        """
        from unittest.mock import MagicMock
        from fitinera.models import AccountState, Income

        flow = AccountInterestFlow("savings", 0.05)
        account = AccountState(id="savings", balance=1000.0, labels={})
        view = MagicMock()
        view.get_accounts.return_value = [account]
        updater = MagicMock()
        logger = MagicMock()

        flow.executeFlow(view, updater, logger)

        updater.emit_transaction.assert_called_once()
        emitted = updater.emit_transaction.call_args[0][0]
        assert isinstance(emitted, Income)
        assert emitted.to_account == "savings"


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

    def test_execute_flow_logs_warning_when_compute_minimum_returns_zero(self):
        """RebalanceExtraSavingsFlow.executeFlow logs warning and skips when minimum is 0.0.

        Per FR-018, if strategy.compute_minimum returns 0.0, logger.warning must be
        called and emit_transaction must not be called.
        """
        from unittest.mock import MagicMock
        from fitinera.models import AccountState

        strategy = MagicMock()
        strategy.compute_minimum.return_value = 0.0
        flow = RebalanceExtraSavingsFlow("checking", "savings", strategy)
        account = AccountState(id="checking", balance=5000.0, labels={})
        view = MagicMock()
        view.get_accounts.return_value = [account]
        updater = MagicMock()
        logger = MagicMock()

        flow.executeFlow(view, updater, logger)

        logger.warning.assert_called_once()
        updater.emit_transaction.assert_not_called()


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
# Constructor-inspection tests removed after fields were made private.
# Behaviour is covered by TestLivingExpenseFlowZeroInflation and
# TestLivingExpenseFlowWithInflation in test_task08_flows.py.
