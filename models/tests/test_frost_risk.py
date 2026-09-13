import pytest

from models.frost_risk import assess_frost_risk


def test_no_risk_well_above_threshold():
    result = assess_frost_risk(forecast_low_f=50, stage="full_bloom")
    assert result.level == "none"


def test_watch_between_10pct_and_90pct_kill():
    # full_bloom: 10% kill at 28F, 90% kill at 25F -> 27F is in between
    result = assess_frost_risk(forecast_low_f=27, stage="full_bloom")
    assert result.level == "watch"


def test_warning_at_or_below_90pct_kill():
    result = assess_frost_risk(forecast_low_f=25, stage="full_bloom")
    assert result.level == "warning"
    result_colder = assess_frost_risk(forecast_low_f=20, stage="full_bloom")
    assert result_colder.level == "warning"


def test_dormant_buds_are_far_more_cold_hardy_than_full_bloom():
    # Same 25F reading: warning at full bloom, but no risk at all while
    # still a dormant swollen bud (10% kill only at 17F for that stage).
    bloom = assess_frost_risk(forecast_low_f=25, stage="full_bloom")
    dormant = assess_frost_risk(forecast_low_f=25, stage="dormant_swollen_bud")
    assert bloom.level == "warning"
    assert dormant.level == "none"


def test_unknown_stage_raises():
    with pytest.raises(ValueError):
        assess_frost_risk(forecast_low_f=30, stage="not_a_real_stage")
