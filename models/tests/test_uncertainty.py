import numpy as np
import pandas as pd
import pytest

from models.uncertainty import (
    MonteCarloResult,
    draw_systematic_temp_bias,
    draw_hargreaves_structural_error_in,
    perturb_hourly_series,
    perturb_daily_minmax,
    TEMP_SENSOR_SYSTEMATIC_BIAS_STD_F,
)


def test_monte_carlo_result_percentiles_and_summary():
    values = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    result = MonteCarloResult(values)
    assert result.percentile(50) == pytest.approx(3.0)
    summary = result.summary()
    assert summary["n_trials"] == 5
    assert summary["mean"] == pytest.approx(3.0)


def test_systematic_bias_drawn_once_per_trial_not_per_reading():
    # The mechanism under test: perturb_hourly_series adds ONE bias value
    # uniformly to an entire series, so every reading in a trial shifts by
    # exactly the same amount -- unlike iid per-reading noise, the spread
    # (max-min) of the series is completely unchanged by the perturbation.
    rng = np.random.default_rng(42)
    idx = pd.date_range("2024-01-01", periods=24, freq="h")
    temps = pd.Series(np.linspace(30, 50, 24), index=idx)
    bias = draw_systematic_temp_bias(rng, n=1)[0]

    perturbed = perturb_hourly_series(temps, bias)
    original_spread = temps.max() - temps.min()
    perturbed_spread = perturbed.max() - perturbed.min()
    assert perturbed_spread == pytest.approx(original_spread)
    assert (perturbed - temps).nunique() == 1  # every reading shifted by the same amount


def test_systematic_bias_distribution_matches_documented_std():
    rng = np.random.default_rng(7)
    biases = draw_systematic_temp_bias(rng, n=50_000)
    assert biases.mean() == pytest.approx(0.0, abs=0.02)
    assert biases.std() == pytest.approx(TEMP_SENSOR_SYSTEMATIC_BIAS_STD_F, rel=0.05)


def test_zero_bias_leaves_series_unchanged():
    idx = pd.date_range("2024-01-01", periods=5, freq="h")
    temps = pd.Series([40.0, 41.0, 42.0, 43.0, 44.0], index=idx)
    perturbed = perturb_hourly_series(temps, bias_f=0.0)
    pd.testing.assert_series_equal(perturbed, temps)


def test_perturb_daily_minmax_shifts_both_by_same_bias():
    idx = pd.date_range("2024-01-01", periods=3, freq="D")
    tmin = pd.Series([30.0, 32.0, 34.0], index=idx)
    tmax = pd.Series([50.0, 52.0, 54.0], index=idx)
    new_min, new_max = perturb_daily_minmax(tmin, tmax, bias_f=1.5)
    assert (new_min - tmin == 1.5).all()
    assert (new_max - tmax == 1.5).all()
    # spread (tmax - tmin) unaffected by a shared bias
    assert ((new_max - new_min) == (tmax - tmin)).all()


def test_hargreaves_structural_error_is_independent_per_trial():
    rng = np.random.default_rng(3)
    errors = draw_hargreaves_structural_error_in(rng, n=10_000)
    assert errors.mean() == pytest.approx(0.0, abs=0.002)
    assert len(np.unique(errors)) == len(errors)  # not a single shared draw like sensor bias
