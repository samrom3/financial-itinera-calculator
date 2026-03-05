from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True, kw_only=True)
class Transaction:
    """Atomic, immutable record of value movement."""

    amount: float
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, kw_only=True)
class Income(Transaction):
    """Money flowing into the system from an external source."""

    to_account: str


@dataclass(frozen=True, kw_only=True)
class Expense(Transaction):
    """Money flowing out of the system to an external destination."""

    from_account: str


@dataclass(frozen=True, kw_only=True)
class Transfer(Transaction):
    """Money moving within the system from one account to another."""

    from_account: str
    to_account: str
