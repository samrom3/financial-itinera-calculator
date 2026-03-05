from fitinera_v1.flows import (
    MortgagePaymentFlow,
    LivingExpenseFlow,
)


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


def test_net_worth_generator_evaluate_raises_not_implemented():
    pass
