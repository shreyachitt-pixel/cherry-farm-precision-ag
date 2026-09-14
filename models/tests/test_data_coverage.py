import pandas as pd
import pytest

from models.data_coverage import has_adequate_coverage


def test_full_hourly_coverage_passes():
    idx = pd.date_range("2024-01-01", "2024-01-10", freq="h")
    assert has_adequate_coverage(idx, pd.Timestamp("2024-01-02"), pd.Timestamp("2024-01-05"), expected_per_day=24)


def test_completely_unrelated_data_window_fails():
    # The exact real bug this module was built to catch: data exists,
    # but not anywhere near the requested window.
    idx = pd.date_range("2025-11-01", "2026-09-01", freq="h")
    assert not has_adequate_coverage(idx, pd.Timestamp("2020-11-01"), pd.Timestamp("2021-05-01"), expected_per_day=24)


def test_empty_index_fails():
    idx = pd.DatetimeIndex([])
    assert not has_adequate_coverage(idx, pd.Timestamp("2024-01-01"), pd.Timestamp("2024-01-10"), expected_per_day=24)


def test_partial_coverage_below_threshold_fails():
    # Only ~50% of expected hourly readings present in-window.
    idx = pd.date_range("2024-01-01", "2024-01-05", freq="2h")
    assert not has_adequate_coverage(idx, pd.Timestamp("2024-01-01"), pd.Timestamp("2024-01-05"), expected_per_day=24, min_fraction=0.9)


def test_partial_coverage_above_lowered_threshold_passes():
    idx = pd.date_range("2024-01-01", "2024-01-05", freq="2h")
    assert has_adequate_coverage(idx, pd.Timestamp("2024-01-01"), pd.Timestamp("2024-01-05"), expected_per_day=24, min_fraction=0.4)


def test_daily_coverage_works_with_expected_per_day_one():
    idx = pd.date_range("2024-06-01", "2024-08-31", freq="D")
    assert has_adequate_coverage(idx, pd.Timestamp("2024-06-01"), pd.Timestamp("2024-08-31"), expected_per_day=1)
