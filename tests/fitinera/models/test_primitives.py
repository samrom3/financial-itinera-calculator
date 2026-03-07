"""Tests for primitive value types: Age, Date, Label, Metric, TurnDuration, ElapsedDuration."""

import pytest
from fitinera.models import Age, Label, Metric, TurnDuration, ElapsedDuration


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

    def test_turn_duration_holds_years_and_months(self):
        """TurnDuration stores years and optional months fields."""
        td = TurnDuration(years=2, months=6)
        assert td.years == 2
        assert td.months == 6


class TestElapsedDuration:
    """Tests for ElapsedDuration dataclass."""

    def test_elapsed_duration_months_stored_correctly(self):
        """ElapsedDuration stores the given months value."""
        ed = ElapsedDuration(months=15)
        assert ed.months == 15

    def test_years_property_returns_floor_division_by_12(self):
        """ElapsedDuration.years is floor(months / 12)."""
        assert ElapsedDuration(months=0).years == 0
        assert ElapsedDuration(months=11).years == 0
        assert ElapsedDuration(months=12).years == 1
        assert ElapsedDuration(months=13).years == 1
        assert ElapsedDuration(months=24).years == 2
        assert ElapsedDuration(months=25).years == 2

    def test_years_frac_property_returns_months_divided_by_12(self):
        """ElapsedDuration.years_frac is months / 12 as a float."""
        assert ElapsedDuration(months=0).years_frac == 0.0
        assert ElapsedDuration(months=6).years_frac == pytest.approx(0.5)
        assert ElapsedDuration(months=12).years_frac == pytest.approx(1.0)
        assert ElapsedDuration(months=18).years_frac == pytest.approx(1.5)

    def test_elapsed_duration_is_frozen(self):
        """ElapsedDuration is a frozen dataclass."""
        ed = ElapsedDuration(months=5)
        with pytest.raises(Exception):
            ed.months = 10  # type: ignore[misc]
