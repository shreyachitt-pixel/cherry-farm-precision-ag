import pandas as pd

from models.chill import (
    cumulative_chill_hours,
    chill_requirement_met_date,
    is_chill_hour,
)


def test_is_chill_hour_bounds():
    assert is_chill_hour(40.0) is True
    assert is_chill_hour(45.0) is True  # inclusive upper bound
    assert is_chill_hour(46.0) is False
    assert is_chill_hour(31.0) is False  # below default lower bound
    assert is_chill_hour(31.0, lower_bound_f=None) is True  # no lower bound


def test_cumulative_chill_hours_counts_only_qualifying_hours():
    idx = pd.date_range("2026-01-01", periods=5, freq="h")
    temps = pd.Series([40.0, 50.0, 44.0, 30.0, 45.0], index=idx)
    # qualifying: 40 (yes), 50 (no), 44 (yes), 30 (no, below lower bound), 45 (yes)
    cum = cumulative_chill_hours(temps, start=idx[0])
    assert list(cum) == [1, 1, 2, 2, 3]


def test_cumulative_chill_hours_zero_before_start():
    idx = pd.date_range("2026-01-01", periods=4, freq="h")
    temps = pd.Series([40.0, 40.0, 40.0, 40.0], index=idx)
    cum = cumulative_chill_hours(temps, start=idx[2])
    assert list(cum) == [0, 0, 1, 2]


def test_chill_requirement_met_date():
    idx = pd.date_range("2026-01-01", periods=10, freq="h")
    temps = pd.Series([40.0] * 10, index=idx)
    met = chill_requirement_met_date(temps, start=idx[0], required_hours=5)
    assert met == idx[4]


def test_chill_requirement_never_met_returns_none():
    idx = pd.date_range("2026-01-01", periods=3, freq="h")
    temps = pd.Series([40.0, 40.0, 40.0], index=idx)
    met = chill_requirement_met_date(temps, start=idx[0], required_hours=100)
    assert met is None
