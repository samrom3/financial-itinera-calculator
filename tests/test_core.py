import pytest
from fitinera.core import Age, TimeBounds, MonthlyGrowth, AnnualGrowth, Month


def test_age_creation():
    age = Age(30, Month.JUNE)
    assert age.year == 30
    assert age.month == Month.JUNE


def test_age_invalid_year():
    with pytest.raises(ValueError, match="Year must be non-negative."):
        Age(-1, Month.JUNE)


def test_age_comparison():
    assert Age(30, Month.JUNE) < Age(31, Month.JUNE)
    assert Age(30, Month.JUNE) < Age(30, Month.JULY)
    assert Age(30, Month.JUNE) == Age(30, Month.JUNE)


def test_time_bounds_creation():
    time_bounds = TimeBounds(start=Age(30, Month.JANUARY), end=Age(65, Month.JANUARY))
    assert time_bounds.start == Age(30, Month.JANUARY)
    assert time_bounds.end == Age(65, Month.JANUARY)


def test_time_bounds_invalid_range():
    with pytest.raises(ValueError, match="Start age cannot be after end age."):
        TimeBounds(start=Age(65, Month.JANUARY), end=Age(30, Month.JANUARY))


def test_monthly_growth():
    growth = MonthlyGrowth(annual_rate=0.12)
    assert growth.get_monthly_growth_rate(Month.JUNE) == pytest.approx(0.01)


def test_annual_growth_creation():
    growth = AnnualGrowth(annual_rate=0.12, month_of_year=Month.APRIL)
    assert growth.annual_rate == 0.12
    assert growth.month_of_year == Month.APRIL


def test_annual_growth_rate():
    growth = AnnualGrowth(annual_rate=0.12, month_of_year=Month.APRIL)
    assert growth.get_monthly_growth_rate(Month.APRIL) == 0.12
    assert growth.get_monthly_growth_rate(Month.MAY) == 0.0
