"""
Uncertainty sources for the pipeline, and the Monte Carlo mechanics to
propagate them through chill/GDD/ETo instead of reporting single point
predictions.

Two real, cited sources of uncertainty, kept distinct because they behave
differently:

1. SENSOR MEASUREMENT UNCERTAINTY (temperature). CIMIS doesn't publish a
   per-station instrument spec for station 262, so this uses the accuracy
   of the Vaisala HMP-series temperature/RH probes commonly deployed in
   ag weather networks of this kind as a representative bound: +/-0.2C
   (+/-0.36F) -- see Vaisala HMP7/HMP8/HMP155 datasheets. This is a
   REPRESENTATIVE instrument-class figure, not a confirmed spec for this
   exact station -- flagged here rather than presented as more certain
   than it is.

2. MODEL (STRUCTURAL) UNCERTAINTY in the Hargreaves-Samani ETo formula
   itself, independent of how well temperature is measured: published
   RMSE of the uncalibrated Hargreaves method against Penman-Monteith
   reference ETo in Mediterranean climates (the closest documented
   analog to Lodi's climate) is 0.65-1.38 mm/day across sites. Even a
   perfectly measured temperature still feeds a formula that's only
   this accurate.

A key design choice: sensor bias is drawn ONCE PER MONTE CARLO TRIAL and
applied uniformly across the whole real hourly series for that trial, not
resampled independently at every hour. A fixed, installed sensor that's
off by +0.15C reads +0.15C high all day, every day -- it's a correlated
(systematic) error, not independent per-reading noise. Treating it as iid
noise per timestep would let errors partially cancel out when the model
sums/accumulates readings (chill hours, cumulative GDD), understating the
real uncertainty in exactly the quantities this project cares about most.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

# Representative instrument-class accuracy (Vaisala HMP-series datasheets),
# treated as an approximate 1-sigma bound for the per-deployment
# calibration offset -- see module docstring for the sourcing caveat.
TEMP_SENSOR_SYSTEMATIC_BIAS_STD_F = 0.36

# Uncalibrated Hargreaves-Samani RMSE vs. Penman-Monteith, Mediterranean
# climate sites (closest documented analog to Lodi) -- literature range
# 0.65-1.38 mm/day; using the midpoint as the representative 1-sigma
# structural-error bound.
HARGREAVES_ETO_RMSE_MM_PER_DAY = 1.0
MM_PER_INCH = 25.4


@dataclass
class MonteCarloResult:
    values: np.ndarray

    def percentile(self, p: float) -> float:
        return float(np.percentile(self.values, p))

    def summary(self) -> dict:
        return {
            "median": self.percentile(50),
            "p5": self.percentile(5),
            "p95": self.percentile(95),
            "mean": float(np.mean(self.values)),
            "std": float(np.std(self.values)),
            "n_trials": len(self.values),
        }


def draw_systematic_temp_bias(rng: np.random.Generator, n: int) -> np.ndarray:
    """One bias value per trial (not per reading) -- see module docstring."""
    return rng.normal(0.0, TEMP_SENSOR_SYSTEMATIC_BIAS_STD_F, size=n)


def draw_hargreaves_structural_error_in(rng: np.random.Generator, n: int) -> np.ndarray:
    """Independent per trial -- this represents the formula's own inherent
    inaccuracy, not a per-timestep sensor artifact, so there's no
    correlated-vs-independent distinction to make here the way there is
    for sensor bias."""
    rmse_in = HARGREAVES_ETO_RMSE_MM_PER_DAY / MM_PER_INCH
    return rng.normal(0.0, rmse_in, size=n)


def perturb_hourly_series(hourly_temp_f: pd.Series, bias_f: float) -> pd.Series:
    return hourly_temp_f + bias_f


def perturb_daily_minmax(tmin_f: pd.Series, tmax_f: pd.Series, bias_f: float) -> tuple[pd.Series, pd.Series]:
    return tmin_f + bias_f, tmax_f + bias_f
