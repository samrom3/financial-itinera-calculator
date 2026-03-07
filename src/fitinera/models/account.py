from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass(frozen=True)
class Account:
    """A store of monetary value in the simulation system.

    Frozen snapshot type used in Turn history and SimulationScenario.
    The engine maintains mutable AccountState objects for live balances;
    Account instances are produced at turn-end as immutable records.
    """

    id: str
    initial_balance: float
    labels: Dict[str, str] = field(default_factory=dict)

    @property
    def balance(self) -> float:
        """Returns the account's balance (equals initial_balance for snapshot types)."""
        return self.initial_balance

    def get_label(self, facet: str) -> Optional[str]:
        """Returns the label value for the given facet, or None if absent."""
        return self.labels.get(facet)


@dataclass
class AccountState:
    """Mutable live account state maintained by the engine during a simulation run.

    Unlike the frozen Account snapshot, AccountState is updated in-place as
    transactions are applied. Flows receive AccountState objects from
    SimulationStateView.get_accounts() and must not mutate them directly —
    all mutations are performed by SimulationStateUpdater.emit_transaction().
    """

    id: str
    balance: float
    labels: Dict[str, str] = field(default_factory=dict)

    def get_label(self, facet: str) -> Optional[str]:
        """Returns the label value for the given facet, or None if absent."""
        return self.labels.get(facet)
