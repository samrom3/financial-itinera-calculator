from dataclasses import dataclass, field
from typing import Dict, Optional
from .primitives import Age


@dataclass(frozen=True)
class Person:
    """Represents individuals in the simulation."""

    id: str
    age: Age
    expectancy: Age
    labels: Dict[str, str] = field(default_factory=dict)

    def living(self) -> bool:
        raise NotImplementedError("Pending implementation")

    def get_label(self, facet: str) -> Optional[str]:
        raise NotImplementedError("Pending implementation")
