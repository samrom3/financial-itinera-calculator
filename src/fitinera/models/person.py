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
        """Returns True if current age is strictly less than life expectancy.

        Comparison is lexicographic on (years, months): living if
        age.years < expectancy.years, or age.years == expectancy.years
        and age.months < expectancy.months.
        """
        if self.age.years < self.expectancy.years:
            return True
        if self.age.years == self.expectancy.years:
            return self.age.months < self.expectancy.months
        return False

    def get_label(self, facet: str) -> Optional[str]:
        """Returns the label value for the given facet, or None if absent."""
        return self.labels.get(facet)
