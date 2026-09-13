"""
SYNTHETIC DATA — NOT REAL MEASUREMENTS.

Generates a plausible-but-invented hourly Lodi, CA climate series so the
chill/GDD/irrigation pipeline and dashboard can be built and tested before
a CIMIS API key is configured and before enough real farm data exists.

Calibrated loosely to well-known Central Valley climate normals (roughly:
July highs in the low-to-mid 90s F, January highs in the mid-50s F, most
rain falling Nov-Mar, near-zero rain Jun-Aug) via a seasonal sinusoid plus
a diurnal sinusoid plus random noise. These are NOT the actual normals for
any specific station — once CIMIS is wired in (ingestion/cimis_client.py),
this file's output should stop being used for anything except pipeline
tests, and every plot/notebook that touches it should say so.

Output: data/simulated/SYNTHETIC_lodi_climate.csv
Columns: timestamp, air_temp_f, rh_pct, precip_in, wind_mph
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

OUTPUT_PATH = Path(__file__).parent / "SYNTHETIC_lodi_climate.csv"

# Rough seasonal calibration points (NOT sourced from a real station).
# Loosely aimed at Central Valley normals: ~46.5F daily mean / ~38-55F
# range in January, ~75.5F daily mean / ~58-93F range in July.
ANNUAL_MEAN_TEMP_F = 61.0     # average of the daily-mean temperature series
SEASONAL_AMPLITUDE_F = 14.5   # swing of the daily mean above/below that average
WINTER_DIURNAL_HALF_F = 7.0   # half the day/night swing in Jan (smaller: fog/cloud)
SUMMER_DIURNAL_HALF_F = 17.0  # half the day/night swing in Jul (larger: clear/dry)
RNG_SEED = 42


def generate(start: str, end: str, seed: int = RNG_SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    idx = pd.date_range(start, end, freq="h", inclusive="left")
    day_of_year = idx.dayofyear.values
    hour = idx.hour.values

    # Seasonal component (daily mean) peaks near day 202 (~Jul 21), troughs
    # near day 20 (~Jan 20)
    phase = 2 * math.pi * (day_of_year - 111) / 365.25
    seasonal_mean = ANNUAL_MEAN_TEMP_F + SEASONAL_AMPLITUDE_F * np.sin(phase)
    # Diurnal half-swing also varies seasonally: bigger in clear dry summer,
    # smaller in foggy/cloudy winter. Same phase as the seasonal mean.
    diurnal_half = (
        (WINTER_DIURNAL_HALF_F + SUMMER_DIURNAL_HALF_F) / 2
        + (SUMMER_DIURNAL_HALF_F - WINTER_DIURNAL_HALF_F) / 2 * np.sin(phase)
    )
    # Diurnal cycle peaks mid-afternoon (~4pm), troughs before dawn (~5am)
    diurnal = diurnal_half * np.sin(2 * math.pi * (hour - 9) / 24)
    noise = rng.normal(0, 2.5, size=len(idx))
    air_temp_f = seasonal_mean + diurnal + noise

    # Relative humidity: inversely related to temp, higher in winter, with noise
    rh_pct = np.clip(
        85 - 0.55 * (air_temp_f - 50) + rng.normal(0, 5, size=len(idx)), 15, 100
    )

    # Precip: concentrated Nov-Mar, rare and light otherwise. Simple day-level
    # Bernoulli draw per calendar day, spread across a few hours when it hits.
    is_wet_season = np.isin(idx.month, [11, 12, 1, 2, 3])
    daily_rain_chance = np.where(is_wet_season, 0.18, 0.02)
    rain_draw = rng.random(size=len(idx)) < (daily_rain_chance / 24)  # per-hour approx
    precip_in = np.where(rain_draw, rng.exponential(0.05, size=len(idx)), 0.0)

    wind_mph = np.clip(rng.normal(6, 3, size=len(idx)), 0, None)

    df = pd.DataFrame(
        {
            "timestamp": idx,
            "air_temp_f": air_temp_f.round(1),
            "rh_pct": rh_pct.round(1),
            "precip_in": precip_in.round(3),
            "wind_mph": wind_mph.round(1),
        }
    )
    return df


def main() -> None:
    df = generate(start="2025-11-01", end="2026-10-01")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"Wrote {len(df)} SYNTHETIC hourly rows to {OUTPUT_PATH}")
    print("This is fabricated data for pipeline testing only — see data/README.md")


if __name__ == "__main__":
    main()
