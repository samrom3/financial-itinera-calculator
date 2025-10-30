from __future__ import annotations
from dataclasses import dataclass

from .core import Age


@dataclass(frozen=True)
class TimeHorizon:
    """Defines the time horizon for a financial simulation."""

    current_age: Age
    life_expectancy: Age

    def __post_init__(self):
        if self.current_age >= self.life_expectancy:
            raise ValueError("Current age must be less than life expectancy.")


@dataclass(frozen=True)
class RetirementGoal:
    """Defines the retirement goal for a financial simulation."""

    retirement_age: Age
    desired_estate_value: float = 0.0

    def __post_init__(self):
        if self.desired_estate_value < 0:
            raise ValueError("Desired estate value cannot be negative.")
