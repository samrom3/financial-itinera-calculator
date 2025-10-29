import pytest
from fitinera.core import Age, Month
from fitinera.planning import RetirementGoal, TimeHorizon


def test_time_horizon_post_init_valid():
    time_horizon = TimeHorizon(current_age=Age(30, Month.JANUARY), life_expectancy=Age(95, Month.JANUARY))
    assert time_horizon.current_age == Age(30, Month.JANUARY)
    assert time_horizon.life_expectancy == Age(95, Month.JANUARY)


def test_time_horizon_post_init_invalid():
    with pytest.raises(ValueError, match="Current age must be less than life expectancy."):
        TimeHorizon(current_age=Age(95, Month.JANUARY), life_expectancy=Age(95, Month.JANUARY))
    with pytest.raises(ValueError, match="Current age must be less than life expectancy."):
        TimeHorizon(current_age=Age(96, Month.JANUARY), life_expectancy=Age(95, Month.JANUARY))


def test_retirement_goal_post_init_valid():
    retirement_goal = RetirementGoal(retirement_age=Age(65, Month.JANUARY), desired_estate_value=1_000_000)
    assert retirement_goal.retirement_age == Age(65, Month.JANUARY)
    assert retirement_goal.desired_estate_value == 1_000_000


def test_retirement_goal_post_init_invalid_desired_estate_value():
    with pytest.raises(ValueError, match="Desired estate value cannot be negative."):
        RetirementGoal(retirement_age=Age(65, Month.JANUARY), desired_estate_value=-1)
