import pandas as pd

from models.gdd import daily_gdd, cumulative_gdd


def test_daily_gdd_simple_case():
    # base 39F, tmin 45, tmax 65 -> mean 55 -> gdd = 16
    assert daily_gdd(tmin_f=45.0, tmax_f=65.0, base_f=39.0) == 16.0


def test_daily_gdd_clamps_below_base():
    # tmin below base gets clamped up to base before averaging
    # base 39, tmin 30 (clamped to 39), tmax 49 -> mean 44 -> gdd = 5
    assert daily_gdd(tmin_f=30.0, tmax_f=49.0, base_f=39.0) == 5.0


def test_daily_gdd_never_negative():
    assert daily_gdd(tmin_f=20.0, tmax_f=30.0, base_f=39.0) == 0.0


def test_cumulative_gdd_accumulates_and_respects_start():
    idx = pd.date_range("2026-03-01", periods=4, freq="D")
    tmin = pd.Series([45.0, 45.0, 45.0, 45.0], index=idx)
    tmax = pd.Series([65.0, 65.0, 65.0, 65.0], index=idx)
    cum = cumulative_gdd(tmin, tmax, start=idx[1], base_f=39.0)
    # day0 zeroed by start cutoff, days 1-3 each contribute 16
    assert list(cum) == [0.0, 16.0, 32.0, 48.0]
