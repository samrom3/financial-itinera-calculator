"""Tests for Account and AccountState models."""

import pytest
from fitinera.models import Account, AccountState


class TestAccountBalance:
    """Tests for Account.balance property."""

    def test_balance_returns_initial_balance(self):
        """Account.balance returns initial_balance when no mutations occur.

        Account is a frozen snapshot type; its balance is always its initial value.
        """
        acc = Account(id="checking", initial_balance=500.0)
        assert acc.balance == 500.0

    def test_balance_returns_zero_when_initial_balance_is_zero(self):
        """Account.balance returns 0.0 for a zero-balance account."""
        acc = Account(id="savings", initial_balance=0.0)
        assert acc.balance == 0.0

    def test_balance_returns_negative_when_initial_balance_is_negative(self):
        """Account.balance correctly represents a liability (negative balance)."""
        acc = Account(id="mortgage", initial_balance=-300_000.0)
        assert acc.balance == -300_000.0


class TestAccountGetLabel:
    """Tests for Account.get_label() method."""

    def test_get_label_returns_value_for_existing_facet(self):
        """Account.get_label returns the label value for a known facet."""
        acc = Account(id="checking", initial_balance=0.0, labels={"Type": "ASSET"})
        assert acc.get_label("Type") == "ASSET"

    def test_get_label_returns_none_for_missing_facet(self):
        """Account.get_label returns None when the facet is not present."""
        acc = Account(id="checking", initial_balance=0.0, labels={"Type": "ASSET"})
        assert acc.get_label("Category") is None

    def test_get_label_returns_none_when_labels_empty(self):
        """Account.get_label returns None when the labels dict is empty."""
        acc = Account(id="checking", initial_balance=100.0)
        assert acc.get_label("Type") is None


class TestAccountState:
    """Tests for AccountState dataclass shape and behaviour."""

    def test_account_state_has_required_fields(self):
        """AccountState can be constructed with id, balance, and labels."""
        state = AccountState(id="checking", balance=1_000.0, labels={"Type": "ASSET"})
        assert state.id == "checking"
        assert state.balance == 1_000.0
        assert state.labels == {"Type": "ASSET"}

    def test_account_state_balance_is_mutable(self):
        """AccountState.balance can be reassigned (it is not frozen)."""
        state = AccountState(id="checking", balance=100.0, labels={})
        state.balance = 200.0
        assert state.balance == 200.0

    def test_account_state_default_labels_is_empty_dict(self):
        """AccountState labels defaults to an empty dict when not supplied."""
        state = AccountState(id="savings", balance=0.0)
        assert state.labels == {}

    def test_account_state_get_label_raises_not_implemented(self):
        """AccountState.get_label raises NotImplementedError (stub, implemented in story-02)."""
        state = AccountState(id="checking", balance=0.0, labels={"Type": "ASSET"})
        with pytest.raises(NotImplementedError):
            state.get_label("Type")
