"""Tests for primitive value types: Age, Date, Label, Metric, TurnDuration."""

import pytest
from fitinera.models import Age, Label, Metric, TurnDuration


class TestAge:
    """Tests for Age dataclass."""

    def test_age_cannot_be_mutated(self):
        """Age is a frozen dataclass and raises FrozenInstanceError on mutation attempt."""
        age = Age(years=30)
        with pytest.raises(Exception):
            age.years = 31  # type: ignore[misc]


class TestLabel:
    """Tests for Label dataclass."""

    def test_label_current_value_returns_expected_string(self):
        """Label.current_value() returns the stored value string."""
        label = Label(facet="Status", value="Working")
        assert label.current_value() == "Working"


class TestMetric:
    """Tests for Metric dataclass."""

    def test_metric_is_frozen(self):
        """Metric is a frozen dataclass and raises FrozenInstanceError on mutation attempt."""
        metric = Metric(name="NetWorth", value=100_000.0)
        with pytest.raises(Exception):
            metric.value = 200_000.0  # type: ignore[misc]


class TestTurnDuration:
    """Tests for TurnDuration dataclass."""

    def test_of_yields_correct_total_months(self):
        """TurnDuration.of(years=2, months=6) stores 30 total months."""
        td = TurnDuration.of(years=2, months=6)
        assert td.months == 30

    def test_years_property_returns_floor_division_by_12(self):
        """TurnDuration.years is floor(months / 12)."""
        assert TurnDuration(months=0).years == 0
        assert TurnDuration(months=11).years == 0
        assert TurnDuration(months=12).years == 1
        assert TurnDuration(months=13).years == 1
        assert TurnDuration(months=24).years == 2
        assert TurnDuration(months=25).years == 2

    def test_years_frac_property_returns_months_divided_by_12(self):
        """TurnDuration.years_frac is months / 12 as a float."""
        assert TurnDuration(months=0).years_frac == 0.0
        assert TurnDuration(months=6).years_frac == pytest.approx(0.5)
        assert TurnDuration(months=12).years_frac == pytest.approx(1.0)
        assert TurnDuration(months=18).years_frac == pytest.approx(1.5)

    def test_years_months_property_returns_tuple(self):
        """TurnDuration.years_months returns (whole_years, remaining_months)."""
        assert TurnDuration(months=30).years_months == (2, 6)
        assert TurnDuration(months=12).years_months == (1, 0)
        assert TurnDuration(months=0).years_months == (0, 0)

    def test_turn_duration_is_frozen(self):
        """TurnDuration is a frozen dataclass."""
        td = TurnDuration(months=5)
        with pytest.raises(Exception):
            td.months = 10  # type: ignore[misc]

    def test_of_years_only(self):
        """TurnDuration.of(years=3) stores 36 total months."""
        td = TurnDuration.of(years=3)
        assert td.months == 36

    def test_of_months_only(self):
        """TurnDuration.of(months=7) stores 7 total months."""
        td = TurnDuration.of(months=7)
        assert td.months == 7
