"""Tests for task-08 Flow implementations.

Covers executeFlow() and compute_minimum() behavior for:
  - PersonRetirementLabelFlow (lifecycle.py)
  - ConditionalLabelFlow (lifecycle.py)
  - AccountSolvencyGuardFlow (risk.py)
  - AccountInterestFlow (investments.py)
  - CurrentTurnExpenseStrategy (investments.py)
  - RollingAverageExpenseStrategy (investments.py)
  - RebalanceExtraSavingsFlow (investments.py)
  - LivingExpenseFlow zero-inflation path (spending.py)
  - LivingExpenseFlow inflation path (spending.py)
  - MortgagePaymentFlow (debt.py)

TDD cycle: tests written first (red), then implementation (green).
"""

from unittest.mock import MagicMock

from fitinera.flows.lifecycle import PersonRetirementLabelFlow, ConditionalLabelFlow
from fitinera.flows.risk import AccountSolvencyGuardFlow
from fitinera.flows.investments import (
    CurrentTurnExpenseStrategy,
    RollingAverageExpenseStrategy,
    AccountInterestFlow,
    RebalanceExtraSavingsFlow,
)
from fitinera.flows.spending import LivingExpenseFlow
from fitinera.flows.debt import MortgagePaymentFlow
from fitinera.models import AccountState, Expense, Transfer, Income, TurnDuration


# ---------------------------------------------------------------------------
# PersonRetirementLabelFlow — executeFlow() behavior
# ---------------------------------------------------------------------------


class TestPersonRetirementLabelFlowExecute:
    """Tests for PersonRetirementLabelFlow.executeFlow() behavior."""

    def test_updates_all_person_labels_when_condition_true(self):
        """PersonRetirementLabelFlow updates labels for all person_ids when condition is True.

        When condition.evaluate(view) is True, update_person_label must be called
        for each person_id in person_ids with the configured facet and value.
        """
        condition = MagicMock()
        condition.evaluate.return_value = True
        flow = PersonRetirementLabelFlow(["alice", "bob"], condition)
        view = MagicMock()
        updater = MagicMock()
        logger = MagicMock()

        flow.executeFlow(view, updater, logger)

        updater.update_person_label.assert_any_call("alice", "Status", "Retired")
        updater.update_person_label.assert_any_call("bob", "Status", "Retired")
        assert updater.update_person_label.call_count == 2

    def test_does_not_update_labels_when_condition_false(self):
        """PersonRetirementLabelFlow does nothing when condition is False.

        When condition.evaluate(view) is False, update_person_label must not be called.
        """
        condition = MagicMock()
        condition.evaluate.return_value = False
        flow = PersonRetirementLabelFlow(["alice"], condition)
        view = MagicMock()
        updater = MagicMock()
        logger = MagicMock()

        flow.executeFlow(view, updater, logger)

        updater.update_person_label.assert_not_called()

    def test_logs_info_when_condition_true(self):
        """PersonRetirementLabelFlow logs info when updating labels.

        When condition is True and labels are updated, logger.info must be called at
        least once (FR-020 observability).
        """
        condition = MagicMock()
        condition.evaluate.return_value = True
        flow = PersonRetirementLabelFlow(["alice"], condition)
        view = MagicMock()
        updater = MagicMock()
        logger = MagicMock()

        flow.executeFlow(view, updater, logger)

        logger.info.assert_called()

    def test_uses_custom_status_facet_and_retired_value(self):
        """PersonRetirementLabelFlow applies custom facet and value when condition is True.

        Constructor-provided status_facet and retired_value must be used in
        update_person_label calls instead of defaults.
        """
        condition = MagicMock()
        condition.evaluate.return_value = True
        flow = PersonRetirementLabelFlow(
            ["alice"], condition, status_facet="LifeStage", retired_value="FIRE"
        )
        view = MagicMock()
        updater = MagicMock()
        logger = MagicMock()

        flow.executeFlow(view, updater, logger)

        updater.update_person_label.assert_called_once_with(
            "alice", "LifeStage", "FIRE"
        )

    def test_evaluates_condition_with_view(self):
        """PersonRetirementLabelFlow calls condition.evaluate with the view argument.

        The condition must be evaluated with the same view passed to executeFlow.
        """
        condition = MagicMock()
        condition.evaluate.return_value = False
        flow = PersonRetirementLabelFlow(["alice"], condition)
        view = MagicMock()
        updater = MagicMock()
        logger = MagicMock()

        flow.executeFlow(view, updater, logger)

        condition.evaluate.assert_called_once_with(view)


# ---------------------------------------------------------------------------
# ConditionalLabelFlow — executeFlow() behavior
# ---------------------------------------------------------------------------


class TestConditionalLabelFlowExecute:
    """Tests for ConditionalLabelFlow.executeFlow() behavior."""

    def test_updates_person_label_when_condition_true(self):
        """ConditionalLabelFlow calls update_person_label when condition is True.

        When condition.evaluate(view) is True, update_person_label must be called
        with the configured person_id, facet, and value.
        """
        condition = MagicMock()
        condition.evaluate.return_value = True
        flow = ConditionalLabelFlow(condition, "alice", "Status", "Active")
        view = MagicMock()
        updater = MagicMock()
        logger = MagicMock()

        flow.executeFlow(view, updater, logger)

        updater.update_person_label.assert_called_once_with("alice", "Status", "Active")

    def test_does_not_update_label_when_condition_false(self):
        """ConditionalLabelFlow does nothing when condition is False.

        When condition.evaluate(view) is False, update_person_label must not be called.
        """
        condition = MagicMock()
        condition.evaluate.return_value = False
        flow = ConditionalLabelFlow(condition, "alice", "Status", "Active")
        view = MagicMock()
        updater = MagicMock()
        logger = MagicMock()

        flow.executeFlow(view, updater, logger)

        updater.update_person_label.assert_not_called()

    def test_evaluates_condition_with_view(self):
        """ConditionalLabelFlow calls condition.evaluate with the view argument.

        The condition must be evaluated with the same view passed to executeFlow.
        """
        condition = MagicMock()
        condition.evaluate.return_value = False
        flow = ConditionalLabelFlow(condition, "alice", "Status", "Active")
        view = MagicMock()
        updater = MagicMock()
        logger = MagicMock()

        flow.executeFlow(view, updater, logger)

        condition.evaluate.assert_called_once_with(view)


# ---------------------------------------------------------------------------
# AccountSolvencyGuardFlow — executeFlow() behavior
# ---------------------------------------------------------------------------


class TestAccountSolvencyGuardFlowExecute:
    """Tests for AccountSolvencyGuardFlow.executeFlow() behavior."""

    def test_raises_for_asset_account_with_negative_balance(self):
        """AccountSolvencyGuardFlow raises SolvencyViolationError for negative ASSET balance.

        When an account has get_label('Type') == 'ASSET' and balance < 0,
        SolvencyViolationError must be raised with the account id and balance in the message.
        """
        from fitinera.engine.result import SolvencyViolationError

        flow = AccountSolvencyGuardFlow()
        account = AccountState(id="checking", balance=-100.0, labels={"Type": "ASSET"})
        view = MagicMock()
        view.get_accounts.return_value = [account]
        updater = MagicMock()
        logger = MagicMock()

        result = flow.executeFlow(view, updater, logger)

        assert isinstance(result, SolvencyViolationError)
        error_msg = result.message()
        assert "checking" in error_msg
        assert "-100" in error_msg or "-100.0" in error_msg

    def test_no_error_for_asset_account_with_positive_balance(self):
        """AccountSolvencyGuardFlow does not log error for ASSET with positive balance.

        Accounts with non-negative balance are not in violation; logger.error
        must not be called.
        """
        flow = AccountSolvencyGuardFlow()
        account = AccountState(id="checking", balance=500.0, labels={"Type": "ASSET"})
        view = MagicMock()
        view.get_accounts.return_value = [account]
        updater = MagicMock()
        logger = MagicMock()

        flow.executeFlow(view, updater, logger)

        logger.error.assert_not_called()

    def test_no_error_for_asset_account_with_zero_balance(self):
        """AccountSolvencyGuardFlow does not log error for ASSET with zero balance.

        Zero balance is not negative; logger.error must not be called.
        """
        flow = AccountSolvencyGuardFlow()
        account = AccountState(id="checking", balance=0.0, labels={"Type": "ASSET"})
        view = MagicMock()
        view.get_accounts.return_value = [account]
        updater = MagicMock()
        logger = MagicMock()

        flow.executeFlow(view, updater, logger)

        logger.error.assert_not_called()

    def test_liability_account_with_negative_balance_does_not_trigger_guard(self):
        """AccountSolvencyGuardFlow does not flag LIABILITY accounts.

        A LIABILITY account with negative balance must NOT trigger logger.error
        (FR-014: only ASSET-labeled accounts are guarded).
        """
        flow = AccountSolvencyGuardFlow()
        account = AccountState(
            id="mortgage", balance=-200_000.0, labels={"Type": "LIABILITY"}
        )
        view = MagicMock()
        view.get_accounts.return_value = [account]
        updater = MagicMock()
        logger = MagicMock()

        flow.executeFlow(view, updater, logger)

        logger.error.assert_not_called()

    def test_unlabeled_account_with_negative_balance_does_not_trigger_guard(self):
        """AccountSolvencyGuardFlow does not flag accounts without Type label.

        An account with no 'Type' label must not trigger logger.error.
        """
        flow = AccountSolvencyGuardFlow()
        account = AccountState(id="escrow", balance=-50.0, labels={})
        view = MagicMock()
        view.get_accounts.return_value = [account]
        updater = MagicMock()
        logger = MagicMock()

        flow.executeFlow(view, updater, logger)

        logger.error.assert_not_called()

    def test_raises_for_first_violating_asset_account(self):
        """AccountSolvencyGuardFlow raises SolvencyViolationError on the first violating ASSET account.

        When multiple ASSET accounts have negative balances, execution halts at the first
        violation via SolvencyViolationError — no further accounts are inspected.
        """
        from fitinera.engine.result import SolvencyViolationError

        flow = AccountSolvencyGuardFlow()
        accounts = [
            AccountState(id="checking", balance=-100.0, labels={"Type": "ASSET"}),
            AccountState(id="savings", balance=-50.0, labels={"Type": "ASSET"}),
        ]
        view = MagicMock()
        view.get_accounts.return_value = accounts
        updater = MagicMock()
        logger = MagicMock()

        result = flow.executeFlow(view, updater, logger)

        assert isinstance(result, SolvencyViolationError)
        assert "checking" in result.message()

    def test_custom_asset_label_facet_and_value(self):
        """AccountSolvencyGuardFlow uses custom asset_label_facet and asset_label_value.

        An account matching the custom facet/value and having negative balance raises
        SolvencyViolationError; an account matching the default 'Type'/'ASSET' does not.
        """
        from fitinera.engine.result import SolvencyViolationError

        flow = AccountSolvencyGuardFlow(
            asset_label_facet="Category", asset_label_value="CASH"
        )
        account = AccountState(id="wallet", balance=-5.0, labels={"Category": "CASH"})
        view = MagicMock()
        view.get_accounts.return_value = [account]
        updater = MagicMock()
        logger = MagicMock()

        result = flow.executeFlow(view, updater, logger)

        assert isinstance(result, SolvencyViolationError)
        assert "wallet" in result.message()


# ---------------------------------------------------------------------------
# AccountInterestFlow — executeFlow() behavior
# ---------------------------------------------------------------------------


class TestAccountInterestFlowExecute:
    """Tests for AccountInterestFlow.executeFlow() behavior."""

    def test_emits_income_with_correct_monthly_interest(self):
        """AccountInterestFlow emits Income with monthly compound interest amount.

        Monthly rate = (1 + annual_rate)^(1/12) - 1; Income amount = balance * monthly_rate.
        """
        flow = AccountInterestFlow("savings", annual_rate=0.12)
        account = AccountState(id="savings", balance=1_000.0, labels={})
        view = MagicMock()
        view.get_accounts.return_value = [account]
        updater = MagicMock()
        logger = MagicMock()

        flow.executeFlow(view, updater, logger)

        monthly_rate = (1 + 0.12) ** (1 / 12) - 1
        expected_amount = 1_000.0 * monthly_rate
        updater.emit_transaction.assert_called_once()
        emitted = updater.emit_transaction.call_args[0][0]
        assert isinstance(emitted, Income)
        assert abs(emitted.amount - expected_amount) < 1e-9
        assert emitted.to_account == "savings"

    def test_emits_income_even_when_balance_is_zero(self):
        """AccountInterestFlow emits Income of 0.0 when balance is zero (FR-015).

        Zero-balance accounts still emit an Income transaction each turn.
        """
        flow = AccountInterestFlow("savings", annual_rate=0.05)
        account = AccountState(id="savings", balance=0.0, labels={})
        view = MagicMock()
        view.get_accounts.return_value = [account]
        updater = MagicMock()
        logger = MagicMock()

        flow.executeFlow(view, updater, logger)

        updater.emit_transaction.assert_called_once()
        emitted = updater.emit_transaction.call_args[0][0]
        assert isinstance(emitted, Income)
        assert emitted.amount == 0.0

    def test_looks_up_account_by_account_id(self):
        """AccountInterestFlow uses view.get_accounts() to find its account.

        The correct account must be found by matching its id against account_id.
        """
        flow = AccountInterestFlow("savings", annual_rate=0.05)
        other_account = AccountState(id="checking", balance=500.0, labels={})
        savings_account = AccountState(id="savings", balance=2_000.0, labels={})
        view = MagicMock()
        view.get_accounts.return_value = [other_account, savings_account]
        updater = MagicMock()
        logger = MagicMock()

        flow.executeFlow(view, updater, logger)

        emitted = updater.emit_transaction.call_args[0][0]
        monthly_rate = (1 + 0.05) ** (1 / 12) - 1
        assert abs(emitted.amount - 2_000.0 * monthly_rate) < 1e-9


# ---------------------------------------------------------------------------
# CurrentTurnExpenseStrategy — compute_minimum() behavior
# ---------------------------------------------------------------------------


class TestCurrentTurnExpenseStrategyCompute:
    """Tests for CurrentTurnExpenseStrategy.compute_minimum() behavior."""

    def test_returns_sum_of_matching_expenses_times_multiplier(self):
        """CurrentTurnExpenseStrategy returns total matching expenses * multiplier.

        Only Expense transactions with from_account == from_account are summed.
        """
        from fitinera.models import Expense

        strategy = CurrentTurnExpenseStrategy(expense_multiplier=3.0)
        expense1 = Expense(amount=1000.0, from_account="checking")
        expense2 = Expense(amount=500.0, from_account="checking")
        view = MagicMock()
        view.get_current_turn_transactions.return_value = [expense1, expense2]

        result = strategy.compute_minimum(view, "checking")

        assert abs(result - 4500.0) < 1e-9  # (1000 + 500) * 3.0

    def test_ignores_expenses_for_different_account(self):
        """CurrentTurnExpenseStrategy ignores expenses for other accounts.

        Only expenses where from_account == the from_account argument are counted.
        """
        from fitinera.models import Expense

        strategy = CurrentTurnExpenseStrategy(expense_multiplier=2.0)
        expense_checking = Expense(amount=1000.0, from_account="checking")
        expense_savings = Expense(amount=500.0, from_account="savings")
        view = MagicMock()
        view.get_current_turn_transactions.return_value = [
            expense_checking,
            expense_savings,
        ]

        result = strategy.compute_minimum(view, "savings")

        assert abs(result - 1000.0) < 1e-9  # 500 * 2.0

    def test_returns_zero_when_no_matching_expenses(self):
        """CurrentTurnExpenseStrategy returns 0.0 when no matching expenses (FR-016).

        If no Expense transactions match from_account, the result is 0.0.
        """
        view = MagicMock()
        view.get_current_turn_transactions.return_value = []
        strategy = CurrentTurnExpenseStrategy()

        result = strategy.compute_minimum(view, "checking")

        assert result == 0.0

    def test_ignores_non_expense_transactions(self):
        """CurrentTurnExpenseStrategy skips Income and Transfer transactions.

        Only Expense instances are counted; Income and Transfer are ignored.
        """
        from fitinera.models import Income, Transfer

        strategy = CurrentTurnExpenseStrategy(expense_multiplier=1.0)
        income = Income(amount=5000.0, to_account="checking")
        transfer = Transfer(
            amount=1000.0, from_account="checking", to_account="savings"
        )
        view = MagicMock()
        view.get_current_turn_transactions.return_value = [income, transfer]

        result = strategy.compute_minimum(view, "checking")

        assert result == 0.0


# ---------------------------------------------------------------------------
# RollingAverageExpenseStrategy — compute_minimum() behavior
# ---------------------------------------------------------------------------


class TestRollingAverageExpenseStrategyCompute:
    """Tests for RollingAverageExpenseStrategy.compute_minimum() behavior."""

    def test_returns_mean_of_deque_times_multiplier(self):
        """RollingAverageExpenseStrategy returns mean(deque) * multiplier.

        After two calls with expenses 1000 and 2000, the mean is 1500 * multiplier.
        """
        from fitinera.models import Expense

        strategy = RollingAverageExpenseStrategy(
            lookback_months=6, expense_multiplier=2.0
        )

        view1 = MagicMock()
        view1.get_current_turn_transactions.return_value = [
            Expense(amount=1000.0, from_account="checking")
        ]
        view2 = MagicMock()
        view2.get_current_turn_transactions.return_value = [
            Expense(amount=2000.0, from_account="checking")
        ]

        strategy.compute_minimum(view1, "checking")
        result = strategy.compute_minimum(view2, "checking")

        assert abs(result - 3000.0) < 1e-9  # mean(1000, 2000) * 2.0 = 1500 * 2.0

    def test_returns_zero_when_deque_is_empty(self):
        """RollingAverageExpenseStrategy returns 0.0 when deque is empty (FR-017).

        Before any transactions are seen, compute_minimum must return 0.0.
        """
        strategy = RollingAverageExpenseStrategy(lookback_months=6)
        view = MagicMock()
        view.get_current_turn_transactions.return_value = []

        result = strategy.compute_minimum(view, "checking")

        assert result == 0.0

    def test_deque_respects_lookback_months(self):
        """RollingAverageExpenseStrategy discards values beyond lookback_months.

        With lookback_months=2, only the two most recent turns are averaged.
        """
        from fitinera.models import Expense

        strategy = RollingAverageExpenseStrategy(
            lookback_months=2, expense_multiplier=1.0
        )

        amounts = [1000.0, 2000.0, 3000.0]
        for amount in amounts:
            view = MagicMock()
            view.get_current_turn_transactions.return_value = [
                Expense(amount=amount, from_account="checking")
            ]
            result = strategy.compute_minimum(view, "checking")

        # After 3 calls with lookback=2, deque holds [2000, 3000]
        # mean = 2500, * 1.0 = 2500
        assert abs(result - 2500.0) < 1e-9

    def test_appends_zero_for_turn_with_no_matching_expenses(self):
        """RollingAverageExpenseStrategy appends 0.0 to deque when no expenses match.

        A turn with no matching expenses still contributes 0.0 to the rolling average.
        """
        from fitinera.models import Expense

        strategy = RollingAverageExpenseStrategy(
            lookback_months=2, expense_multiplier=1.0
        )

        view_with_expense = MagicMock()
        view_with_expense.get_current_turn_transactions.return_value = [
            Expense(amount=2000.0, from_account="checking")
        ]
        view_no_expense = MagicMock()
        view_no_expense.get_current_turn_transactions.return_value = []

        strategy.compute_minimum(view_with_expense, "checking")
        result = strategy.compute_minimum(view_no_expense, "checking")

        # deque: [2000, 0] → mean = 1000 * 1.0
        assert abs(result - 1000.0) < 1e-9


# ---------------------------------------------------------------------------
# RebalanceExtraSavingsFlow — executeFlow() behavior
# ---------------------------------------------------------------------------


class TestRebalanceExtraSavingsFlowExecute:
    """Tests for RebalanceExtraSavingsFlow.executeFlow() behavior."""

    def test_emits_transfer_when_balance_exceeds_minimum(self):
        """RebalanceExtraSavingsFlow emits Transfer for excess savings.

        When balance > strategy.compute_minimum(), the excess must be transferred
        to to_account.
        """
        strategy = MagicMock()
        strategy.compute_minimum.return_value = 3000.0
        flow = RebalanceExtraSavingsFlow("checking", "savings", strategy)
        account = AccountState(id="checking", balance=5000.0, labels={})
        view = MagicMock()
        view.get_accounts.return_value = [account]
        updater = MagicMock()
        logger = MagicMock()

        flow.executeFlow(view, updater, logger)

        updater.emit_transaction.assert_called_once()
        emitted = updater.emit_transaction.call_args[0][0]
        assert isinstance(emitted, Transfer)
        assert emitted.from_account == "checking"
        assert emitted.to_account == "savings"
        assert abs(emitted.amount - 2000.0) < 1e-9  # 5000 - 3000

    def test_does_not_emit_transfer_when_balance_equals_minimum(self):
        """RebalanceExtraSavingsFlow does not transfer when balance equals minimum.

        Exact minimum balance produces no transfer (no excess).
        """
        strategy = MagicMock()
        strategy.compute_minimum.return_value = 5000.0
        flow = RebalanceExtraSavingsFlow("checking", "savings", strategy)
        account = AccountState(id="checking", balance=5000.0, labels={})
        view = MagicMock()
        view.get_accounts.return_value = [account]
        updater = MagicMock()
        logger = MagicMock()

        flow.executeFlow(view, updater, logger)

        updater.emit_transaction.assert_not_called()

    def test_does_not_emit_transfer_when_balance_below_minimum(self):
        """RebalanceExtraSavingsFlow does not transfer when balance is below minimum.

        No excess to transfer.
        """
        strategy = MagicMock()
        strategy.compute_minimum.return_value = 8000.0
        flow = RebalanceExtraSavingsFlow("checking", "savings", strategy)
        account = AccountState(id="checking", balance=5000.0, labels={})
        view = MagicMock()
        view.get_accounts.return_value = [account]
        updater = MagicMock()
        logger = MagicMock()

        flow.executeFlow(view, updater, logger)

        updater.emit_transaction.assert_not_called()

    def test_logs_warning_when_compute_minimum_returns_zero(self):
        """RebalanceExtraSavingsFlow logs warning and returns when compute_minimum is 0.0.

        Per FR-018, if compute_minimum returns 0.0, log a warning and skip transfer.
        """
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

    def test_calls_strategy_with_view_and_from_account(self):
        """RebalanceExtraSavingsFlow calls strategy.compute_minimum with correct args.

        The strategy must receive the view and from_account identifier.
        """
        strategy = MagicMock()
        strategy.compute_minimum.return_value = 1000.0
        flow = RebalanceExtraSavingsFlow("checking", "savings", strategy)
        account = AccountState(id="checking", balance=500.0, labels={})
        view = MagicMock()
        view.get_accounts.return_value = [account]
        updater = MagicMock()
        logger = MagicMock()

        flow.executeFlow(view, updater, logger)

        strategy.compute_minimum.assert_called_once_with(view, "checking")


# ---------------------------------------------------------------------------
# LivingExpenseFlow — zero-inflation path
# ---------------------------------------------------------------------------


class TestLivingExpenseFlowZeroInflation:
    """Tests for LivingExpenseFlow.executeFlow() with no inflation (default)."""

    def test_emits_expense_with_configured_amount(self):
        """LivingExpenseFlow emits Expense with the configured amount.

        With annual_inflation_rate == 0.0 (default), fixed amount is emitted.
        """
        flow = LivingExpenseFlow(from_account="checking", amount=2000.0)
        view = MagicMock()
        updater = MagicMock()
        logger = MagicMock()

        flow.executeFlow(view, updater, logger)

        updater.emit_transaction.assert_called_once_with(
            Expense(amount=2000.0, from_account="checking")
        )

    def test_emits_expense_unconditionally(self):
        """LivingExpenseFlow emits unconditionally without consulting view state.

        The flow must emit the same Expense every turn regardless of state.
        """
        flow = LivingExpenseFlow(from_account="savings", amount=500.0)
        view = MagicMock()
        updater = MagicMock()
        logger = MagicMock()

        flow.executeFlow(view, updater, logger)

        updater.emit_transaction.assert_called_once()
        emitted = updater.emit_transaction.call_args[0][0]
        assert isinstance(emitted, Expense)
        assert emitted.amount == 500.0
        assert emitted.from_account == "savings"


# ---------------------------------------------------------------------------
# LivingExpenseFlow — inflation path (FR-019)
# ---------------------------------------------------------------------------


class TestLivingExpenseFlowWithInflation:
    """Tests for LivingExpenseFlow.executeFlow() with annual_inflation_rate > 0."""

    def test_emits_inflated_expense_on_first_turn(self):
        """LivingExpenseFlow emits inflated Expense using turn_index from elapsed_duration.

        inflated_amount = amount * (1 + annual_inflation_rate) ** (turn_index / 12.0)
        where turn_index = view.get_elapsed_duration().months
        """
        flow = LivingExpenseFlow(
            from_account="checking", amount=1000.0, annual_inflation_rate=0.12
        )
        view = MagicMock()
        view.get_elapsed_duration.return_value = TurnDuration(months=1)
        updater = MagicMock()
        logger = MagicMock()

        flow.executeFlow(view, updater, logger)

        expected_amount = 1000.0 * (1 + 0.12) ** (1 / 12.0)
        updater.emit_transaction.assert_called_once()
        emitted = updater.emit_transaction.call_args[0][0]
        assert isinstance(emitted, Expense)
        assert abs(emitted.amount - expected_amount) < 1e-9
        assert emitted.from_account == "checking"

    def test_emits_inflated_expense_at_turn_12(self):
        """LivingExpenseFlow correctly inflates over 12 months.

        At turn_index=12, one full year of effective annual inflation is applied.
        """
        flow = LivingExpenseFlow(
            from_account="checking", amount=2000.0, annual_inflation_rate=0.06
        )
        view = MagicMock()
        view.get_elapsed_duration.return_value = TurnDuration(months=12)
        updater = MagicMock()
        logger = MagicMock()

        flow.executeFlow(view, updater, logger)

        expected_amount = 2000.0 * (1 + 0.06) ** (12 / 12.0)
        emitted = updater.emit_transaction.call_args[0][0]
        assert abs(emitted.amount - expected_amount) < 1e-9

    def test_emits_flat_expense_at_turn_index_zero(self):
        """LivingExpenseFlow emits the base amount at turn_index=0 (no inflation applied).

        (1 + r) ** 0 == 1, so the amount is unchanged at the very first turn.
        """
        flow = LivingExpenseFlow(
            from_account="checking", amount=1500.0, annual_inflation_rate=0.03
        )
        view = MagicMock()
        view.get_elapsed_duration.return_value = TurnDuration(months=0)
        updater = MagicMock()
        logger = MagicMock()

        flow.executeFlow(view, updater, logger)

        emitted = updater.emit_transaction.call_args[0][0]
        assert abs(emitted.amount - 1500.0) < 1e-9


# ---------------------------------------------------------------------------
# MortgagePaymentFlow — executeFlow() behavior
# ---------------------------------------------------------------------------


class TestMortgagePaymentFlowExecute:
    """Tests for MortgagePaymentFlow.executeFlow() behavior."""

    def test_emits_transfer_with_configured_fields(self):
        """MortgagePaymentFlow emits Transfer with from_account, to_account, and amount.

        emit_transaction must be called exactly once with the configured values.
        """
        flow = MortgagePaymentFlow("checking", "mortgage", 1500.0)
        view = MagicMock()
        updater = MagicMock()
        logger = MagicMock()

        flow.executeFlow(view, updater, logger)

        updater.emit_transaction.assert_called_once_with(
            Transfer(amount=1500.0, from_account="checking", to_account="mortgage")
        )

    def test_emits_transfer_unconditionally(self):
        """MortgagePaymentFlow emits Transfer every turn without consulting state.

        Mortgage payments are fixed unconditional obligations.
        """
        flow = MortgagePaymentFlow("checking", "lender", 800.0)
        view = MagicMock()
        updater = MagicMock()
        logger = MagicMock()

        flow.executeFlow(view, updater, logger)

        updater.emit_transaction.assert_called_once()
        emitted = updater.emit_transaction.call_args[0][0]
        assert isinstance(emitted, Transfer)
        assert emitted.from_account == "checking"
        assert emitted.to_account == "lender"
        assert emitted.amount == 800.0
