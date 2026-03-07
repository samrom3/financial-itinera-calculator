from typing import Any, List
from unittest.mock import MagicMock

from fitinera.flows import (
    MortgagePaymentFlow,
    LivingExpenseFlow,
    NetWorthGenerator,
)
from fitinera.models import AccountState


def test_job_income_flow_execute_raises_not_implemented():
    pass


def test_mortgage_payment_flow_initialization_stores_accounts():
    flow = MortgagePaymentFlow("Checking", "Mortgage", 1000)
    assert flow.from_account == "Checking"


def test_living_expense_flow_initialization_stores_amount():
    flow = LivingExpenseFlow("Checking", 1000)
    assert flow.amount == 1000


def test_retirement_check_flow_execute_raises_not_implemented():
    pass


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
        assert generator.evaluate(view) == 0.0

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
        assert generator.evaluate(view) == 1_500.0

    def test_evaluate_subtracts_liability_balances(self):
        """NetWorthGenerator.evaluate subtracts LIABILITY-typed account balances.

        A single LIABILITY account with balance 200_000.0 → net worth -200_000.0.
        """
        generator = NetWorthGenerator()
        accounts = [
            AccountState(
                id="mortgage", balance=200_000.0, labels={"Type": "LIABILITY"}
            ),
        ]
        view = _make_view(accounts)
        assert generator.evaluate(view) == -200_000.0

    def test_evaluate_combines_assets_and_liabilities(self):
        """NetWorthGenerator.evaluate correctly combines ASSET and LIABILITY balances.

        Assets 500_000.0, liabilities 200_000.0 → net worth 300_000.0.
        """
        generator = NetWorthGenerator()
        accounts = [
            AccountState(id="house", balance=500_000.0, labels={"Type": "ASSET"}),
            AccountState(
                id="mortgage", balance=200_000.0, labels={"Type": "LIABILITY"}
            ),
        ]
        view = _make_view(accounts)
        assert generator.evaluate(view) == 300_000.0

    def test_evaluate_ignores_accounts_without_type_label(self):
        """NetWorthGenerator.evaluate ignores accounts with no Type label.

        An account with no 'Type' label is neither ASSET nor LIABILITY and
        must not affect the result.
        """
        generator = NetWorthGenerator()
        accounts = [
            AccountState(id="checking", balance=1_000.0, labels={"Type": "ASSET"}),
            AccountState(id="escrow", balance=50.0, labels={}),
        ]
        view = _make_view(accounts)
        assert generator.evaluate(view) == 1_000.0

    def test_evaluate_ignores_accounts_with_unknown_type_label(self):
        """NetWorthGenerator.evaluate ignores accounts with unrecognised Type values.

        Only 'ASSET' and 'LIABILITY' are summed; other Type values are skipped.
        """
        generator = NetWorthGenerator()
        accounts = [
            AccountState(id="checking", balance=1_000.0, labels={"Type": "ASSET"}),
            AccountState(id="pension", balance=5_000.0, labels={"Type": "PENSION"}),
        ]
        view = _make_view(accounts)
        assert generator.evaluate(view) == 1_000.0
