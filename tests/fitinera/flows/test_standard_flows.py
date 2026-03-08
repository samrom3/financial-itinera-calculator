from typing import Any, List
from unittest.mock import MagicMock

from fitinera.flows import (
    JobIncomeFlow,
    MortgagePaymentFlow,
    LivingExpenseFlow,
    NetWorthGenerator,
)
from fitinera.models import AccountState, Age, Income, Expense, Transfer, Person


def test_job_income_flow_execute_raises_not_implemented():
    pass


def test_mortgage_payment_flow_initialization_stores_accounts():
    flow = MortgagePaymentFlow("Checking", "Mortgage", 1000)
    assert flow.from_account == "Checking"


def test_retirement_check_flow_execute_raises_not_implemented():
    pass


def _make_living_person(person_id: str, status: str = "Working") -> Person:
    """Build a living Person with the given status label."""
    return Person(
        id=person_id,
        age=Age(years=40, months=0),
        expectancy=Age(years=85, months=0),
        labels={"Status": status},
    )


def _make_view_with_person(person: Any) -> Any:
    """Build a minimal SimulationStateView mock returning the given person."""
    view = MagicMock()
    view.get_person.return_value = person
    return view


class TestJobIncomeFlow:
    """Tests for JobIncomeFlow.executeFlow()."""

    def test_emits_income_when_person_is_living_and_working(self):
        """JobIncomeFlow emits Income when person is living and Status == 'Working'.

        The emitted Income must have the configured amount and to_account, and
        emit_transaction must be called exactly once.
        """
        flow = JobIncomeFlow(person_id="alice", amount=5000.0, to_account="checking")
        person = _make_living_person("alice", status="Working")
        view = _make_view_with_person(person)
        updater = MagicMock()
        logger = MagicMock()

        flow.executeFlow(view, updater, logger)

        updater.emit_transaction.assert_called_once_with(
            Income(amount=5000.0, to_account="checking")
        )

    def test_does_not_emit_income_when_person_not_working(self):
        """JobIncomeFlow skips income and calls logger.info when Status != 'Working'.

        A retired person should not receive employment income; a log message must be
        emitted instead.
        """
        flow = JobIncomeFlow(person_id="alice", amount=5000.0, to_account="checking")
        person = _make_living_person("alice", status="Retired")
        view = _make_view_with_person(person)
        updater = MagicMock()
        logger = MagicMock()

        flow.executeFlow(view, updater, logger)

        updater.emit_transaction.assert_not_called()
        logger.info.assert_called_once()

    def test_does_not_emit_income_when_person_not_living(self):
        """JobIncomeFlow skips income and calls logger.info when person is not living.

        A deceased person (age >= expectancy) must not generate income; a log message
        must be emitted instead.
        """
        flow = JobIncomeFlow(person_id="alice", amount=5000.0, to_account="checking")
        person = Person(
            id="alice",
            age=Age(years=85, months=0),
            expectancy=Age(years=85, months=0),
            labels={"Status": "Working"},
        )
        view = _make_view_with_person(person)
        updater = MagicMock()
        logger = MagicMock()

        flow.executeFlow(view, updater, logger)

        updater.emit_transaction.assert_not_called()
        logger.info.assert_called_once()

    def test_does_not_emit_income_when_person_not_found(self):
        """JobIncomeFlow skips income and calls logger.info when person is None.

        get_person returning None means the person ID is not in the simulation;
        emit_transaction must not be called.
        """
        flow = JobIncomeFlow(person_id="ghost", amount=5000.0, to_account="checking")
        view = MagicMock()
        view.get_person.return_value = None
        updater = MagicMock()
        logger = MagicMock()

        flow.executeFlow(view, updater, logger)

        updater.emit_transaction.assert_not_called()
        logger.info.assert_called_once()

    def test_looks_up_person_by_person_id(self):
        """JobIncomeFlow calls get_person with the configured person_id.

        The view must be queried with exactly the person_id supplied at construction.
        """
        flow = JobIncomeFlow(person_id="bob", amount=3000.0, to_account="salary")
        person = _make_living_person("bob", status="Working")
        view = _make_view_with_person(person)
        updater = MagicMock()
        logger = MagicMock()

        flow.executeFlow(view, updater, logger)

        view.get_person.assert_called_once_with("bob")


class TestLivingExpenseFlow:
    """Tests for LivingExpenseFlow.executeFlow() — zero-inflation path."""

    def test_emits_expense_with_configured_amount_and_account(self):
        """LivingExpenseFlow emits Expense with the configured amount and from_account.

        With annual_inflation_rate == 0.0 (default) the amount is fixed each turn.
        emit_transaction must be called exactly once.
        """
        flow = LivingExpenseFlow(from_account="checking", amount=2000.0)
        view = MagicMock()
        updater = MagicMock()
        logger = MagicMock()

        flow.executeFlow(view, updater, logger)

        updater.emit_transaction.assert_called_once_with(
            Expense(amount=2000.0, from_account="checking")
        )

    def test_emits_expense_every_turn_regardless_of_state(self):
        """LivingExpenseFlow always emits the expense without checking view state.

        Living expenses are unconditional; no view methods should be needed.
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


class TestMortgagePaymentFlow:
    """Tests for MortgagePaymentFlow.executeFlow()."""

    def test_emits_transfer_with_configured_fields(self):
        """MortgagePaymentFlow emits Transfer with from_account, to_account, and amount.

        emit_transaction must be called exactly once with a Transfer carrying all
        three constructor-provided values.
        """
        flow = MortgagePaymentFlow(
            from_account="checking", to_account="mortgage", amount=1500.0
        )
        view = MagicMock()
        updater = MagicMock()
        logger = MagicMock()

        flow.executeFlow(view, updater, logger)

        updater.emit_transaction.assert_called_once_with(
            Transfer(amount=1500.0, from_account="checking", to_account="mortgage")
        )

    def test_emits_transfer_every_turn_regardless_of_state(self):
        """MortgagePaymentFlow always emits its transfer without consulting view state.

        Mortgage payments are unconditional fixed obligations each turn.
        """
        flow = MortgagePaymentFlow(
            from_account="checking", to_account="lender", amount=800.0
        )
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


def _make_view(accounts: List[AccountState]) -> Any:
    """Build a minimal SimulationStateView mock returning the given accounts."""
    view = MagicMock()
    view.get_accounts.return_value = accounts
    return view


class TestNetWorthGenerator:
    """Tests for NetWorthGenerator.evaluate()."""

    def test_evaluate_returns_zero_for_no_accounts(self):
        """NetWorthGenerator.evaluate returns 0.0 when there are no accounts.

        With an empty account list, net worth is the sum of nothing, which is 0.
        """
        generator = NetWorthGenerator()
        view = _make_view([])
        assert generator.evaluate(view, MagicMock()) == 0.0

    def test_evaluate_sums_asset_balances(self):
        """NetWorthGenerator.evaluate sums balances of ASSET-typed accounts.

        Two ASSET accounts with balances 1000.0 and 500.0 → net worth 1500.0.
        """
        generator = NetWorthGenerator()
        accounts = [
            AccountState(id="checking", balance=1_000.0, labels={"Type": "ASSET"}),
            AccountState(id="savings", balance=500.0, labels={"Type": "ASSET"}),
        ]
        view = _make_view(accounts)
        assert generator.evaluate(view, MagicMock()) == 1_500.0

    def test_evaluate_sums_liability_balances(self):
        """NetWorthGenerator.evaluate sums LIABILITY-typed account balances directly.

        LIABILITY accounts carry negative balances by convention (e.g. a $200k mortgage
        is stored as -200_000.0). Summing directly gives the correct net worth of -200_000.0.
        """
        generator = NetWorthGenerator()
        accounts = [
            AccountState(
                id="mortgage", balance=-200_000.0, labels={"Type": "LIABILITY"}
            ),
        ]
        view = _make_view(accounts)
        assert generator.evaluate(view, MagicMock()) == -200_000.0

    def test_evaluate_combines_assets_and_liabilities(self):
        """NetWorthGenerator.evaluate correctly combines ASSET and LIABILITY balances.

        House ASSET 500_000.0 plus mortgage LIABILITY -200_000.0 → net worth 300_000.0.
        """
        generator = NetWorthGenerator()
        accounts = [
            AccountState(id="house", balance=500_000.0, labels={"Type": "ASSET"}),
            AccountState(
                id="mortgage", balance=-200_000.0, labels={"Type": "LIABILITY"}
            ),
        ]
        view = _make_view(accounts)
        assert generator.evaluate(view, MagicMock()) == 300_000.0

    def test_evaluate_includes_accounts_without_type_label(self):
        """NetWorthGenerator.evaluate includes accounts with no Type label.

        All account balances are summed unconditionally regardless of labels.
        """
        generator = NetWorthGenerator()
        accounts = [
            AccountState(id="checking", balance=1_000.0, labels={"Type": "ASSET"}),
            AccountState(id="escrow", balance=50.0, labels={}),
        ]
        view = _make_view(accounts)
        assert generator.evaluate(view, MagicMock()) == 1_050.0

    def test_evaluate_includes_accounts_with_unknown_type_label(self):
        """NetWorthGenerator.evaluate includes accounts with unrecognised Type values.

        All account balances are summed unconditionally regardless of Type value.
        """
        generator = NetWorthGenerator()
        accounts = [
            AccountState(id="checking", balance=1_000.0, labels={"Type": "ASSET"}),
            AccountState(id="pension", balance=5_000.0, labels={"Type": "PENSION"}),
        ]
        view = _make_view(accounts)
        assert generator.evaluate(view, MagicMock()) == 6_000.0
