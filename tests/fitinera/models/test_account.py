"""Tests for Account, AccountState, and their typed subclasses."""

import pytest

import fitinera
from fitinera.models import (
    Account,
    AccountState,
    AssetAccount,
    AssetAccountState,
    LiabilityAccount,
    LiabilityAccountState,
)


class TestAccountBalance:
    """Tests for Account.balance property via AssetAccount (concrete subclass)."""

    def test_balance_returns_value_at_construction(self):
        """AssetAccount.balance returns the value passed at construction.

        Account is a frozen snapshot type; its balance is always its construction value.
        AssetAccount is used here as Account is now abstract.
        """
        acc = AssetAccount(id="checking", balance=500.0)
        assert acc.balance == 500.0

    def test_balance_returns_zero_when_balance_is_zero(self):
        """AssetAccount.balance returns 0.0 for a zero-balance account."""
        acc = AssetAccount(id="savings", balance=0.0)
        assert acc.balance == 0.0

    def test_liability_balance_returns_positive_value(self):
        """LiabilityAccount.balance stores debts as positive values."""
        acc = LiabilityAccount(id="mortgage", balance=300_000.0)
        assert acc.balance == 300_000.0


class TestAccountGetLabel:
    """Tests for Account.get_label() method via concrete subclasses."""

    def test_get_label_returns_value_for_existing_facet(self):
        """AssetAccount.get_label returns the label value for a known facet."""
        acc = AssetAccount(id="checking", balance=0.0, labels={"Liquidity": "LIQUID"})
        assert acc.get_label("Liquidity") == "LIQUID"

    def test_get_label_returns_none_for_missing_facet(self):
        """AssetAccount.get_label returns None when the facet is not present."""
        acc = AssetAccount(id="checking", balance=0.0, labels={"Liquidity": "LIQUID"})
        assert acc.get_label("Category") is None

    def test_get_label_returns_none_when_labels_empty(self):
        """AssetAccount.get_label returns None when the labels dict is empty."""
        acc = AssetAccount(id="checking", balance=100.0)
        assert acc.get_label("Type") is None


class TestAccountState:
    """Tests for AccountState dataclass shape and behaviour."""

    def test_account_state_has_required_fields(self):
        """AccountState can be constructed with id, balance, and labels."""
        state = AssetAccountState(
            id="checking", balance=1_000.0, labels={"Liquidity": "LIQUID"}
        )
        assert state.id == "checking"
        assert state.balance == 1_000.0
        assert state.labels == {"Liquidity": "LIQUID"}

    def test_account_state_balance_is_mutable(self):
        """AssetAccountState.balance can be reassigned (it is not frozen)."""
        state = AssetAccountState(id="checking", balance=100.0, labels={})
        state.balance = 200.0
        assert state.balance == 200.0

    def test_account_state_default_labels_is_empty_dict(self):
        """AssetAccountState labels defaults to an empty dict when not supplied."""
        state = AssetAccountState(id="savings", balance=0.0)
        assert state.labels == {}

    def test_account_state_get_label_returns_value_for_existing_facet(self):
        """AssetAccountState.get_label returns the label value for a known facet."""
        state = AssetAccountState(
            id="checking", balance=0.0, labels={"Liquidity": "LIQUID"}
        )
        assert state.get_label("Liquidity") == "LIQUID"

    def test_account_state_get_label_returns_none_for_missing_facet(self):
        """AssetAccountState.get_label returns None when the facet is not present."""
        state = AssetAccountState(
            id="checking", balance=0.0, labels={"Liquidity": "LIQUID"}
        )
        assert state.get_label("Category") is None

    def test_account_state_get_label_returns_none_when_labels_empty(self):
        """AssetAccountState.get_label returns None when labels dict is empty."""
        state = AssetAccountState(id="savings", balance=500.0)
        assert state.get_label("Type") is None


class TestAssetAccountSubclassing:
    """Tests verifying AssetAccount is a proper subclass of Account."""

    def test_asset_account_is_instance_of_account(self):
        """AssetAccount is an instance of Account (subclass relationship holds)."""
        acc = AssetAccount(id="savings", balance=10_000.0)
        assert isinstance(acc, Account)

    def test_liability_account_is_instance_of_account(self):
        """LiabilityAccount is an instance of Account (subclass relationship holds)."""
        acc = LiabilityAccount(id="mortgage", balance=200_000.0)
        assert isinstance(acc, Account)

    def test_asset_account_state_is_instance_of_account_state(self):
        """AssetAccountState is an instance of AccountState."""
        state = AssetAccountState(id="savings", balance=5_000.0)
        assert isinstance(state, AccountState)

    def test_liability_account_state_is_instance_of_account_state(self):
        """LiabilityAccountState is an instance of AccountState."""
        state = LiabilityAccountState(id="mortgage", balance=200_000.0)
        assert isinstance(state, AccountState)


class TestAssetAccountToState:
    """Tests for AssetAccount.to_state() factory method."""

    def test_to_state_returns_asset_account_state(self):
        """AssetAccount.to_state() returns an AssetAccountState instance."""
        acc = AssetAccount(id="savings", balance=5_000.0)
        state = acc.to_state()
        assert isinstance(state, AssetAccountState)

    def test_to_state_preserves_id(self):
        """AssetAccount.to_state() produces a state with the same account id."""
        acc = AssetAccount(id="emergency-fund", balance=3_000.0)
        state = acc.to_state()
        assert state.id == "emergency-fund"

    def test_to_state_preserves_balance(self):
        """AssetAccount.to_state() produces a state with the same initial balance."""
        acc = AssetAccount(id="brokerage", balance=50_000.0)
        state = acc.to_state()
        assert state.balance == 50_000.0

    def test_to_state_preserves_labels(self):
        """AssetAccount.to_state() produces a state with matching labels."""
        acc = AssetAccount(
            id="isa", balance=20_000.0, labels={"Category": "Investment"}
        )
        state = acc.to_state()
        assert state.labels == {"Category": "Investment"}


class TestLiabilityAccountToState:
    """Tests for LiabilityAccount.to_state() factory method."""

    def test_to_state_returns_liability_account_state(self):
        """LiabilityAccount.to_state() returns a LiabilityAccountState instance."""
        acc = LiabilityAccount(id="mortgage", balance=250_000.0)
        state = acc.to_state()
        assert isinstance(state, LiabilityAccountState)

    def test_to_state_preserves_id(self):
        """LiabilityAccount.to_state() produces a state with the same account id."""
        acc = LiabilityAccount(id="car-loan", balance=15_000.0)
        state = acc.to_state()
        assert state.id == "car-loan"

    def test_to_state_preserves_balance(self):
        """LiabilityAccount.to_state() produces a state with the same initial balance."""
        acc = LiabilityAccount(id="student-loan", balance=40_000.0)
        state = acc.to_state()
        assert state.balance == 40_000.0

    def test_to_state_preserves_labels(self):
        """LiabilityAccount.to_state() produces a state with matching labels."""
        acc = LiabilityAccount(
            id="mortgage", balance=250_000.0, labels={"Priority": "High"}
        )
        state = acc.to_state()
        assert state.labels == {"Priority": "High"}


class TestAssetAccountStateToSnapshot:
    """Tests for AssetAccountState.to_snapshot() factory method."""

    def test_to_snapshot_returns_asset_account(self):
        """AssetAccountState.to_snapshot() returns an AssetAccount instance."""
        state = AssetAccountState(id="savings", balance=8_000.0)
        snapshot = state.to_snapshot()
        assert isinstance(snapshot, AssetAccount)

    def test_to_snapshot_preserves_id(self):
        """AssetAccountState.to_snapshot() produces a snapshot with the same id."""
        state = AssetAccountState(id="isa", balance=25_000.0)
        snapshot = state.to_snapshot()
        assert snapshot.id == "isa"

    def test_to_snapshot_preserves_balance(self):
        """AssetAccountState.to_snapshot() produces a snapshot with the current balance."""
        state = AssetAccountState(id="checking", balance=1_500.0)
        snapshot = state.to_snapshot()
        assert snapshot.balance == 1_500.0

    def test_to_snapshot_preserves_labels(self):
        """AssetAccountState.to_snapshot() produces a snapshot with matching labels."""
        state = AssetAccountState(id="isa", balance=12_000.0, labels={"Tax": "ISA"})
        snapshot = state.to_snapshot()
        assert snapshot.labels == {"Tax": "ISA"}


class TestLiabilityAccountStateToSnapshot:
    """Tests for LiabilityAccountState.to_snapshot() factory method."""

    def test_to_snapshot_returns_liability_account(self):
        """LiabilityAccountState.to_snapshot() returns a LiabilityAccount instance."""
        state = LiabilityAccountState(id="mortgage", balance=200_000.0)
        snapshot = state.to_snapshot()
        assert isinstance(snapshot, LiabilityAccount)

    def test_to_snapshot_preserves_id(self):
        """LiabilityAccountState.to_snapshot() produces a snapshot with the same id."""
        state = LiabilityAccountState(id="car-loan", balance=12_000.0)
        snapshot = state.to_snapshot()
        assert snapshot.id == "car-loan"

    def test_to_snapshot_preserves_balance(self):
        """LiabilityAccountState.to_snapshot() produces a snapshot with the current balance."""
        state = LiabilityAccountState(id="credit-card", balance=3_000.0)
        snapshot = state.to_snapshot()
        assert snapshot.balance == 3_000.0

    def test_to_snapshot_preserves_labels(self):
        """LiabilityAccountState.to_snapshot() produces a snapshot with matching labels."""
        state = LiabilityAccountState(
            id="mortgage", balance=200_000.0, labels={"Lender": "Nationwide"}
        )
        snapshot = state.to_snapshot()
        assert snapshot.labels == {"Lender": "Nationwide"}


class TestAssetAccountStateApplyDelta:
    """Tests for AssetAccountState.apply_delta() — natural sign convention."""

    def test_apply_delta_is_callable(self):
        """AssetAccountState.apply_delta exists and is callable."""
        state = AssetAccountState(id="savings", balance=5_000.0)
        assert callable(state.apply_delta)

    def test_apply_delta_positive_increases_balance(self):
        """AssetAccountState.apply_delta(+100) increases balance by 100."""
        state = AssetAccountState(id="savings", balance=5_000.0)
        state.apply_delta(100.0)
        assert state.balance == 5_100.0

    def test_apply_delta_negative_decreases_balance(self):
        """AssetAccountState.apply_delta(-200) decreases balance by 200."""
        state = AssetAccountState(id="savings", balance=5_000.0)
        state.apply_delta(-200.0)
        assert state.balance == 4_800.0

    def test_apply_delta_zero_leaves_balance_unchanged(self):
        """AssetAccountState.apply_delta(0) leaves balance unchanged."""
        state = AssetAccountState(id="savings", balance=5_000.0)
        state.apply_delta(0.0)
        assert state.balance == 5_000.0


class TestLiabilityAccountStateApplyDelta:
    """Tests for LiabilityAccountState.apply_delta() — inverted sign convention."""

    def test_apply_delta_is_callable(self):
        """LiabilityAccountState.apply_delta exists and is callable."""
        state = LiabilityAccountState(id="mortgage", balance=200_000.0)
        assert callable(state.apply_delta)

    def test_apply_delta_positive_decreases_balance(self):
        """LiabilityAccountState.apply_delta(+500) decreases balance by 500 (debt repayment)."""
        state = LiabilityAccountState(id="mortgage", balance=200_000.0)
        state.apply_delta(500.0)
        assert state.balance == 199_500.0

    def test_apply_delta_negative_increases_balance(self):
        """LiabilityAccountState.apply_delta(-300) increases balance by 300 (new debt)."""
        state = LiabilityAccountState(id="mortgage", balance=200_000.0)
        state.apply_delta(-300.0)
        assert state.balance == 200_300.0

    def test_apply_delta_zero_leaves_balance_unchanged(self):
        """LiabilityAccountState.apply_delta(0) leaves balance unchanged."""
        state = LiabilityAccountState(id="mortgage", balance=200_000.0)
        state.apply_delta(0.0)
        assert state.balance == 200_000.0


class TestLiabilityAccountValidator:
    """Tests for LiabilityAccount.__post_init__ balance validator."""

    def test_raises_value_error_for_negative_balance(self):
        """LiabilityAccount raises ValueError when constructed with a negative balance."""
        with pytest.raises(ValueError, match="balance must be >= 0"):
            LiabilityAccount(id="bad-loan", balance=-1.0)

    def test_accepts_zero_balance(self):
        """LiabilityAccount accepts a zero balance without error."""
        acc = LiabilityAccount(id="paid-off", balance=0.0)
        assert acc.balance == 0.0

    def test_accepts_positive_balance(self):
        """LiabilityAccount accepts a positive balance without error."""
        acc = LiabilityAccount(id="mortgage", balance=300_000.0)
        assert acc.balance == 300_000.0


class TestTopLevelImports:
    """Tests verifying all four types are importable from fitinera directly."""

    def test_asset_account_importable_from_fitinera(self):
        """AssetAccount is importable from the top-level fitinera package."""
        assert hasattr(fitinera, "AssetAccount")

    def test_liability_account_importable_from_fitinera(self):
        """LiabilityAccount is importable from the top-level fitinera package."""
        assert hasattr(fitinera, "LiabilityAccount")

    def test_asset_account_state_importable_from_fitinera(self):
        """AssetAccountState is importable from the top-level fitinera package."""
        assert hasattr(fitinera, "AssetAccountState")

    def test_liability_account_state_importable_from_fitinera(self):
        """LiabilityAccountState is importable from the top-level fitinera package."""
        assert hasattr(fitinera, "LiabilityAccountState")
