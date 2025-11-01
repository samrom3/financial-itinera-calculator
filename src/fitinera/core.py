from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum
from typing import Optional


class Month(IntEnum):
    """An enumeration for the months of the year."""

    JANUARY = 1
    FEBRUARY = 2
    MARCH = 3
    APRIL = 4
    MAY = 5
    JUNE = 6
    JULY = 7
    AUGUST = 8
    SEPTEMBER = 9
    OCTOBER = 10
    NOVEMBER = 11
    DECEMBER = 12


@dataclass(frozen=True, order=True)
class Age:
    """Represents a specific point in time by year and month."""

    year: int
    month: Month

    def __post_init__(self):
        if self.year < 0:
            raise ValueError("Year must be non-negative.")

    def next_month(self) -> Age:
        """
        Returns the next month's age.

        :return: The age of the next month.
        """
        if self.month == Month.DECEMBER:
            return Age(self.year + 1, Month.JANUARY)
        return Age(self.year, self.month + 1)


@dataclass(frozen=True)
class TimeBounds:
    """Defines a time range with an optional start and end Age."""

    start: Optional[Age] = None
    end: Optional[Age] = None

    def __post_init__(self):
        if self.start and self.end and self.start > self.end:
            raise ValueError("Start age cannot be after end age.")

    def is_active(self, current_age: Age) -> bool:
        """
        Checks if the current age is within the time bounds.

        :param current_age: The current age to check.
        :return: True if the current age is within the bounds, False otherwise.
        """
        if self.start and current_age < self.start:
            return False
        if self.end and current_age >= self.end:
            return False
        return True


from abc import ABC, abstractmethod


class GrowthStrategy(ABC):
    """Abstract base class for different value growth strategies."""

    @abstractmethod
    def get_monthly_growth_rate(self, current_month: Month) -> float:
        """
        Returns the growth rate for a given month.

        :param current_month: The current month.
        :return: The growth rate for the month.
        """
        pass


@dataclass(frozen=True)
class MonthlyGrowth(GrowthStrategy):
    """Represents a growth strategy with monthly compounding."""

    annual_rate: float

    def get_monthly_growth_rate(self, current_month: Month) -> float:
        return self.annual_rate / 12


@dataclass(frozen=True)
class AnnualGrowth(GrowthStrategy):
    """Represents a growth strategy with annual compounding in a specific month."""

    annual_rate: float
    month_of_year: Month

    def get_monthly_growth_rate(self, current_month: Month) -> float:
        return self.annual_rate if current_month == self.month_of_year else 0.0


@dataclass(frozen=True)
class NoGrowth(GrowthStrategy):
    """Represents a strategy with no growth, always returning 0."""

    def get_monthly_growth_rate(self, current_month: Month) -> float:
        return 0.0
