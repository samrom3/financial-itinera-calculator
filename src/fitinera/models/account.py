from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass(frozen=True)
class Account(ABC):
    """Abstract frozen snapshot of a monetary account.

    Account is an immutable type used in Turn history and SimulationScenario
    configuration. The engine maintains mutable AccountState objects for live
    balances; Account instances are produced at turn-end as immutable records.

    Concrete subclasses (AssetAccount, LiabilityAccount) must implement
    to_state() to produce the corresponding mutable AccountState.
    """

    id: str
    balance: float
    labels: Dict[str, str] = field(default_factory=dict)

    def get_label(self, facet: str) -> Optional[str]:
        """Returns the label value for the given facet, or None if absent."""
        return self.labels.get(facet)

    @abstractmethod
    def to_state(self) -> "AccountState":
        """Produce a mutable AccountState initialised from this snapshot."""


@dataclass
class AccountState(ABC):
    """Abstract mutable live account state maintained by the engine.

    Unlike the frozen Account snapshot, AccountState is updated in-place as
    transactions are applied. Flows receive AccountState objects from
    SimulationStateView.get_accounts() and must not mutate them directly —
    all mutations are performed by SimulationStateUpdater.emit_transaction().

    Concrete subclasses (AssetAccountState, LiabilityAccountState) must
    implement to_snapshot() to produce the corresponding frozen Account.
    """

    id: str
    balance: float
    labels: Dict[str, str] = field(default_factory=dict)

    def get_label(self, facet: str) -> Optional[str]:
        """Returns the label value for the given facet, or None if absent."""
        return self.labels.get(facet)

    @abstractmethod
    def apply_delta(self, delta: float) -> None:
        """Apply a signed balance change to this account.

        Concrete subclasses define how the delta affects the internal balance
        (e.g. asset vs liability sign conventions).

        Args:
            delta: The signed amount to apply.
        """

    @abstractmethod
    def to_snapshot(self) -> Account:
        """Produce a frozen Account snapshot from the current mutable state."""


@dataclass(frozen=True)
class AssetAccount(Account):
    """A frozen snapshot of an asset account (positive-balance account).

    Represents accounts that hold value the simulation owner controls, such as
    savings accounts, investment portfolios, or cash holdings.
    """

    def to_state(self) -> "AssetAccountState":
        """Produce an AssetAccountState initialised from this snapshot.

        Returns:
            An AssetAccountState with id, balance, and labels copied from this
            snapshot, ready for in-place mutation by the engine.
        """
        return AssetAccountState(
            id=self.id, balance=self.balance, labels=dict(self.labels)
        )


@dataclass(frozen=True)
class LiabilityAccount(Account):
    """A frozen snapshot of a liability account (positive-balance convention).

    Represents accounts that track debts owed by the simulation owner, such as
    mortgages, loans, or credit card balances. Balances are stored as positive
    values representing the amount owed (e.g. a $300,000 mortgage is stored as
    300_000.0).
    """

    def __post_init__(self) -> None:
        """Validate that the liability balance is non-negative.

        Raises:
            ValueError: If balance is negative.
        """
        if self.balance < 0:
            raise ValueError(
                f"LiabilityAccount '{self.id}' balance must be >= 0, got {self.balance}"
            )

    def to_state(self) -> "LiabilityAccountState":
        """Produce a LiabilityAccountState initialised from this snapshot.

        Returns:
            A LiabilityAccountState with id, balance, and labels copied from
            this snapshot, ready for in-place mutation by the engine.
        """
        return LiabilityAccountState(
            id=self.id, balance=self.balance, labels=dict(self.labels)
        )


@dataclass
class AssetAccountState(AccountState):
    """Mutable live state of an asset account.

    Maintained by the engine during a simulation run. At turn-end the engine
    calls to_snapshot() to produce an immutable AssetAccount for the Turn record.
    """

    def apply_delta(self, delta: float) -> None:
        """Apply a signed balance change to this asset account.

        Assets use natural sign convention: a positive delta increases the
        balance and a negative delta decreases it.

        Args:
            delta: The signed amount to apply.
        """
        self.balance += delta

    def to_snapshot(self) -> AssetAccount:
        """Produce a frozen AssetAccount snapshot from the current state.

        Returns:
            A frozen AssetAccount with id, balance, and labels copied from
            the current mutable state.
        """
        return AssetAccount(id=self.id, balance=self.balance, labels=dict(self.labels))


@dataclass
class LiabilityAccountState(AccountState):
    """Mutable live state of a liability account.

    Maintained by the engine during a simulation run. At turn-end the engine
    calls to_snapshot() to produce an immutable LiabilityAccount for the Turn
    record.
    """

    def apply_delta(self, delta: float) -> None:
        """Apply a signed balance change to this liability account.

        Liabilities use inverted sign convention: a positive delta (e.g. a
        payment toward the debt) *decreases* the stored balance, and a
        negative delta *increases* it. This inversion keeps the engine
        type-agnostic — it always passes +amount for credits and -amount
        for debits regardless of account type.

        Args:
            delta: The signed amount to apply (inverted before storage).
        """
        self.balance -= delta

    def to_snapshot(self) -> LiabilityAccount:
        """Produce a frozen LiabilityAccount snapshot from the current state.

        Returns:
            A frozen LiabilityAccount with id, balance, and labels copied from
            the current mutable state.
        """
        return LiabilityAccount(
            id=self.id, balance=self.balance, labels=dict(self.labels)
        )
