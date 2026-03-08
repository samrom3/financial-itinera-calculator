import pytest
from fitinera.models import Expense, Income, Transfer


def test_transaction_is_immutable():
    income = Income(amount=100.0, to_account="savings")
    with pytest.raises((AttributeError, TypeError)):
        income.amount = 200.0  # type: ignore[misc]


def test_income_requires_to_account():
    income = Income(amount=500.0, to_account="checking")
    assert income.to_account == "checking"
    assert income.amount == 500.0
    with pytest.raises(TypeError):
        Income(amount=500.0)  # type: ignore[call-arg]


def test_expense_requires_from_account():
    expense = Expense(amount=200.0, from_account="checking")
    assert expense.from_account == "checking"
    assert expense.amount == 200.0
    with pytest.raises(TypeError):
        Expense(amount=200.0)  # type: ignore[call-arg]


def test_transfer_requires_from_and_to_accounts():
    transfer = Transfer(amount=300.0, from_account="checking", to_account="savings")
    assert transfer.from_account == "checking"
    assert transfer.to_account == "savings"
    assert transfer.amount == 300.0
    with pytest.raises(TypeError):
        Transfer(amount=300.0, to_account="savings")  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        Transfer(amount=300.0, from_account="checking")  # type: ignore[call-arg]
