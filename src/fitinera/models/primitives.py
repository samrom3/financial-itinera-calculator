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
    """Duration stored as total months. Use .of() or .from_dates() to construct."""

    months: int

    @classmethod
    def of(cls, *, years: int = 0, months: int = 0) -> "TurnDuration":
        """Construct from years and/or months components."""
        return cls(months=years * 12 + months)

    @classmethod
    def from_dates(cls, *, start: "Date", end: "Date") -> "TurnDuration":
        """Construct from the month difference between two dates."""
        return cls(months=(end.year - start.year) * 12 + (end.month - start.month))

    @property
    def years(self) -> int:
        """Whole years (floor division of months by 12)."""
        return self.months // 12

    @property
    def years_frac(self) -> float:
        """Fractional years (months / 12.0)."""
        return self.months / 12.0

    @property
    def years_months(self) -> "tuple[int, int]":
        """Tuple of (whole_years, remaining_months)."""
        return (self.months // 12, self.months % 12)


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
