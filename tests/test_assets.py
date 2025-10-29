import pytest
from fitinera.assets import Asset, AssetContributionConstraint, Penalty
from fitinera.core import Age, Month, MonthlyGrowth, TimeBounds


def test_penalty_post_init_valid():
    penalty = Penalty(rate=0.1, time_bounds=TimeBounds(end=Age(59, Month.JULY)))
    assert penalty.rate == 0.1
    assert penalty.time_bounds == TimeBounds(end=Age(59, Month.JULY))


def test_penalty_post_init_invalid_rate():
    with pytest.raises(ValueError, match="Penalty rate must be between 0.0 and 1.0."):
        Penalty(rate=1.1, time_bounds=TimeBounds(end=Age(59, Month.JULY)))
    with pytest.raises(ValueError, match="Penalty rate must be between 0.0 and 1.0."):
        Penalty(rate=-0.1, time_bounds=TimeBounds(end=Age(59, Month.JULY)))


def test_asset_contribution_constraint_post_init_valid():
    constraint = AssetContributionConstraint(effective_monthly_max=100)
    assert constraint.effective_monthly_max == 100


def test_asset_contribution_constraint_post_init_invalid_effective_monthly_max():
    with pytest.raises(ValueError, match="Effective monthly max cannot be negative."):
        AssetContributionConstraint(effective_monthly_max=-1)


def test_asset_post_init_valid():
    asset = Asset(
        name="Test Asset",
        initial_value=1000,
        growth_strategy=MonthlyGrowth(annual_rate=0.05),
        contribution_priority=1,
        withdrawal_priority=1,
    )
    assert asset.name == "Test Asset"
    assert asset.initial_value == 1000


def test_asset_post_init_invalid_name():
    with pytest.raises(ValueError, match="Name cannot be empty."):
        Asset(
            name="",
            initial_value=1000,
            growth_strategy=MonthlyGrowth(annual_rate=0.05),
            contribution_priority=1,
            withdrawal_priority=1,
        )


def test_asset_post_init_invalid_initial_value():
    with pytest.raises(ValueError, match="Initial value cannot be negative."):
        Asset(
            name="Test Asset",
            initial_value=-1000,
            growth_strategy=MonthlyGrowth(annual_rate=0.05),
            contribution_priority=1,
            withdrawal_priority=1,
        )


def test_asset_post_init_invalid_contribution_priority():
    with pytest.raises(ValueError, match="Contribution priority must be positive."):
        Asset(
            name="Test Asset",
            initial_value=1000,
            growth_strategy=MonthlyGrowth(annual_rate=0.05),
            contribution_priority=0,
            withdrawal_priority=1,
        )


def test_asset_post_init_invalid_withdrawal_priority():
    with pytest.raises(ValueError, match="Withdrawal priority must be positive."):
        Asset(
            name="Test Asset",
            initial_value=1000,
            growth_strategy=MonthlyGrowth(annual_rate=0.05),
            contribution_priority=1,
            withdrawal_priority=0,
        )
