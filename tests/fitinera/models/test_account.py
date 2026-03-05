import pytest
from fitinera.models import Account


@pytest.mark.skip(reason="Not yet implemented")
def test_account_balance_cannot_be_mutated_directly():
    pass


def test_account_get_label_raises_not_implemented():
    acc = Account("Checking", 100)
    with pytest.raises(NotImplementedError):
        acc.get_label("Type")


def test_account_balance_property_raises_not_implemented():
    acc = Account("Checking", 100)
    with pytest.raises(NotImplementedError):
        _ = acc.balance
