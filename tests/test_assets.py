import pytest
from fitinera.assets import Asset, AssetBuilder, ContributionConstraint, Penalty
from fitinera.core import Age, Month, MonthlyGrowth, NoGrowth, TimeBounds


def test_penalty_post_init_valid():
    penalty = Penalty(rate=0.1, time_bounds=TimeBounds(end=Age(59, Month.JULY)))
    assert penalty.rate == 0.1
    assert penalty.time_bounds == TimeBounds(end=Age(59, Month.JULY))


def test_penalty_post_init_invalid_rate():
    with pytest.raises(ValueError, match="Penalty rate must be between 0.0 and 1.0."):
        Penalty(rate=1.1, time_bounds=TimeBounds(end=Age(59, Month.JULY)))
    with pytest.raises(ValueError, match="Penalty rate must be between 0.0 and 1.0."):
        Penalty(rate=-0.1, time_bounds=TimeBounds(end=Age(59, Month.JULY)))


def test_contribution_constraint_post_init_valid():
    constraint = ContributionConstraint(effective_monthly_max=100)
    assert constraint.effective_monthly_max == 100


def test_contribution_constraint_post_init_invalid_effective_monthly_max():
    with pytest.raises(ValueError, match="Effective monthly max cannot be negative."):
        ContributionConstraint(effective_monthly_max=-1)


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


def test_asset_builder_valid():
    constraint = ContributionConstraint(effective_monthly_max=200)
    penalty = Penalty(rate=0.1, time_bounds=TimeBounds(end=Age(59, Month.JULY)))
    asset = (
        AssetBuilder("Test Asset")
        .with_initial_value(1000)
        .with_growth_strategy(MonthlyGrowth(annual_rate=0.05))
        .with_contribution_priority(2)
        .with_withdrawal_priority(3)
        .with_contribution_constraint(constraint)
        .with_withdrawal_penalty(penalty)
        .build()
    )

    assert asset.name == "Test Asset"
    assert asset.initial_value == 1000
    assert isinstance(asset.growth_strategy, MonthlyGrowth)
    assert asset.contribution_priority == 2
    assert asset.withdrawal_priority == 3
    assert asset.contribution_constraints == [constraint]
    assert asset.withdrawal_penalties == [penalty]


def test_asset_builder_minimal():
    asset = AssetBuilder("Minimal Asset").build()
    assert asset.name == "Minimal Asset"
    assert asset.initial_value == 0.0
    assert isinstance(asset.growth_strategy, NoGrowth)
    assert asset.contribution_priority == 1
    assert asset.withdrawal_priority == 1
    assert asset.contribution_constraints == []
    assert asset.withdrawal_penalties == []


def test_asset_builder_with_strategy():
    asset = (
        AssetBuilder("Asset With Strategy")
        .with_growth_strategy(MonthlyGrowth(annual_rate=0.05))
        .build()
    )
    assert isinstance(asset.growth_strategy, MonthlyGrowth)


def test_asset_builder_triggers_validation():
    with pytest.raises(ValueError, match="Initial value cannot be negative."):
        AssetBuilder("Invalid Asset").with_initial_value(-100).with_growth_strategy(MonthlyGrowth(0.05)).build()
