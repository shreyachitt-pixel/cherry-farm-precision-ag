import pandas as pd
import pytest

from models.hourly_interpolation import simulate_hourly_temps


def test_simulated_hourly_hits_tmin_and_tmax_at_expected_hours():
    dates = pd.date_range("2026-01-01", periods=3, freq="D")
    tmin = pd.Series([40.0, 40.0, 40.0], index=dates)
    tmax = pd.Series([60.0, 60.0, 60.0], index=dates)
    hourly = simulate_hourly_temps(tmin, tmax)

    day2_5am = pd.Timestamp("2026-01-02 05:00:00")
    day2_2pm = pd.Timestamp("2026-01-02 14:00:00")
    assert hourly[day2_5am] == pytest.approx(40.0, abs=0.01)
    assert hourly[day2_2pm] == pytest.approx(60.0, abs=0.01)


def test_simulated_hourly_stays_within_daily_bounds_when_constant():
    # constant tmin/tmax across all days -> curve should never exceed them
    dates = pd.date_range("2026-01-01", periods=4, freq="D")
    tmin = pd.Series([40.0] * 4, index=dates)
    tmax = pd.Series([60.0] * 4, index=dates)
    hourly = simulate_hourly_temps(tmin, tmax)
    assert hourly.min() == pytest.approx(40.0, abs=0.01)
    assert hourly.max() == pytest.approx(60.0, abs=0.01)


def test_simulated_hourly_covers_full_date_range():
    dates = pd.date_range("2026-03-01", periods=5, freq="D")
    tmin = pd.Series([35.0, 38.0, 40.0, 37.0, 36.0], index=dates)
    tmax = pd.Series([55.0, 58.0, 60.0, 57.0, 56.0], index=dates)
    hourly = simulate_hourly_temps(tmin, tmax)
    assert len(hourly) == 5 * 24
    assert hourly.index.min() == pd.Timestamp("2026-03-01 00:00:00")
    assert hourly.index.max() == pd.Timestamp("2026-03-05 23:00:00")
