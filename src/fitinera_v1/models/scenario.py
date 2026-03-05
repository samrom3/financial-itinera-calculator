from dataclasses import dataclass, field
from typing import List
from .person import Person
from .account import Account
from .primitives import Date, Metric
from .transaction import Transaction


@dataclass(frozen=True)
class Turn:
    """An immutable snapshot representing a single discrete time step."""

    date: Date
    accounts: List[Account]
    persons: List[Person]
    transactions: List[Transaction]
    metrics: List[Metric]


@dataclass(frozen=True)
class SimulationScenario:
    """The initial starting state of the Data Model."""

    initial_persons: List[Person] = field(default_factory=list)
    initial_accounts: List[Account] = field(default_factory=list)
