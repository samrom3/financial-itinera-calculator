import pytest
from fitinera.cashflows import (
    Expense,
    ExpenseBuilder,
    Income,
    IncomeBuilder,
    IncomeKind,
    TaxRate,
    TaxRateBuilder,
)
from fitinera.core import MonthlyGrowth, TimeBounds


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


def test_income_builder_valid():
    income = (
        IncomeBuilder("Test Income", 1000)
        .is_passive_income()
        .with_growth_strategy(MonthlyGrowth(annual_rate=0.03))
        .with_time_bounds(TimeBounds())
        .build()
    )
    assert income.name == "Test Income"
    assert income.monthly_amount == 1000
    assert income.kind == IncomeKind.PASSIVE


def test_income_builder_minimal():
    income = IncomeBuilder("Minimal Income", 500).with_growth_strategy(MonthlyGrowth(0.01)).build()
    assert income.name == "Minimal Income"
    assert income.monthly_amount == 500
    assert income.kind == IncomeKind.ACTIVE


def test_income_builder_is_passive_income():
    builder = IncomeBuilder("Test Income", 1000)
    builder.is_passive_income()
    income = builder.with_growth_strategy(MonthlyGrowth(annual_rate=0.03)).build()
    assert income.kind == IncomeKind.PASSIVE


def test_income_builder_missing_growth_strategy():
    with pytest.raises(ValueError, match="Growth strategy must be set before building the income."):
        IncomeBuilder("Test Income", 1000).build()


def test_expense_builder_valid():
    expense = (
        ExpenseBuilder("Test Expense", 500)
        .with_growth_strategy(MonthlyGrowth(annual_rate=0.02))
        .with_time_bounds(TimeBounds())
        .build()
    )
    assert expense.name == "Test Expense"
    assert expense.monthly_amount == 500


def test_expense_builder_missing_growth_strategy():
    with pytest.raises(ValueError, match="Growth strategy must be set before building the expense."):
        ExpenseBuilder("Test Expense", 500).build()


def test_tax_rate_builder_valid():
    tax_rate = TaxRateBuilder(0.22).with_time_bounds(TimeBounds()).build()
    assert tax_rate.rate == 0.22


def test_tax_rate_builder_minimal():
    tax_rate = TaxRateBuilder(0.15).build()
    assert tax_rate.rate == 0.15
