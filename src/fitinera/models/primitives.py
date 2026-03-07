from dataclasses import dataclass


@dataclass(frozen=True)
class Age:
    """Represents an age globally driven by years and months."""

    years: int
    months: int = 0


@dataclass(frozen=True)
class Date:
    """Represents calendar date consisting of year and month."""

    year: int
    month: int


@dataclass(frozen=True)
class TurnDuration:
    """Represents a duration in years and months."""

    years: int
    months: int = 0


@dataclass(frozen=True)
class Label:
    """A lightweight tagging system (Facet: Value)."""

    facet: str
    value: str

    def current_value(self) -> str:
        return self.value


@dataclass(frozen=True)
class Metric:
    """Globally derived numerical or categorical attributes."""

    name: str
    value: float | str


@dataclass(frozen=True)
class ElapsedDuration:
    """Elapsed time since simulation start, expressed in months."""

    months: int

    @property
    def years(self) -> int:
        """Whole years elapsed (floor division of months by 12)."""
        return self.months // 12

    @property
    def years_frac(self) -> float:
        """Fractional years elapsed (months / 12)."""
        return self.months / 12
