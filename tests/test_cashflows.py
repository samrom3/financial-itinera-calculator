import pytest
from fitinera.cashflows import Expense, Income, IncomeKind, TaxRate
from fitinera.core import MonthlyGrowth


def test_income_post_init_valid():
    income = Income(
        name="Test Income",
        monthly_amount=1000,
        kind=IncomeKind.ACTIVE,
        growth_strategy=MonthlyGrowth(annual_rate=0.03),
    )
    assert income.name == "Test Income"
    assert income.monthly_amount == 1000


def test_income_post_init_valid_negative_amount():
    income = Income(
        name="Test Income",
        monthly_amount=-1000,
        kind=IncomeKind.ACTIVE,
        growth_strategy=MonthlyGrowth(annual_rate=0.03),
    )
    assert income.monthly_amount == -1000


def test_income_post_init_invalid_name():
    with pytest.raises(ValueError, match="Name cannot be empty."):
        Income(
            name="",
            monthly_amount=1000,
            kind=IncomeKind.ACTIVE,
            growth_strategy=MonthlyGrowth(annual_rate=0.03),
        )


def test_expense_post_init_valid():
    expense = Expense(
        name="Test Expense",
        monthly_amount=500,
        growth_strategy=MonthlyGrowth(annual_rate=0.02),
    )
    assert expense.name == "Test Expense"
    assert expense.monthly_amount == 500


def test_expense_post_init_valid_negative_amount():
    expense = Expense(
        name="Test Expense",
        monthly_amount=-500,
        growth_strategy=MonthlyGrowth(annual_rate=0.02),
    )
    assert expense.monthly_amount == -500


def test_expense_post_init_invalid_name():
    with pytest.raises(ValueError, match="Name cannot be empty."):
        Expense(
            name="",
            monthly_amount=500,
            growth_strategy=MonthlyGrowth(annual_rate=0.02),
        )


def test_tax_rate_post_init_valid():
    assert TaxRate(rate=0.22).rate == 0.22
    assert TaxRate(rate=0.0).rate == 0.0
    assert TaxRate(rate=-0.5).rate == -0.5


def test_tax_rate_post_init_invalid_rate():
    with pytest.raises(ValueError, match="Tax rate must be between -1.0 and 1.0."):
        TaxRate(rate=1.0)
    with pytest.raises(ValueError, match="Tax rate must be between -1.0 and 1.0."):
        TaxRate(rate=-1.0)
