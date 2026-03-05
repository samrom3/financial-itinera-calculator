from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass(frozen=True)
class Account:
    """A store of monetary value in the simulation system."""

    id: str
    initial_balance: float
    labels: Dict[str, str] = field(default_factory=dict)

    @property
    def balance(self) -> float:
        raise NotImplementedError("Pending implementation")

    def get_label(self, facet: str) -> Optional[str]:
        raise NotImplementedError("Pending implementation")
