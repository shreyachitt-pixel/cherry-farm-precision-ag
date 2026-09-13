"""
Growing degree-day (GDD) accumulation, used here to predict bloom timing
(after the chill requirement is met) and to track progress toward harvest.

Standard "single sine"-free simple method:
    GDD_day = max(((Tmax + Tmin) / 2) - Tbase, 0)
with Tmax/Tmin clamped to Tbase first, which is the common convention to
avoid a day with a cold night and a warm day producing a misleadingly large
value from the raw average alone.

Base temperature for stone fruit is commonly taken as ~39-50F depending on
source/crop; we use 39F (4C) as a documented default and keep it as a
parameter so it can be tuned once local phenology data exists to fit
against (e.g. comparing predicted vs. observed bloom date).
"""

from __future__ import annotations

import pandas as pd

DEFAULT_BASE_TEMP_F = 39.0


def daily_gdd(tmin_f: float, tmax_f: float, base_f: float = DEFAULT_BASE_TEMP_F) -> float:
    tmin_clamped = max(tmin_f, base_f)
    tmax_clamped = max(tmax_f, base_f)
    return max(((tmax_clamped + tmin_clamped) / 2) - base_f, 0.0)


def cumulative_gdd(
    daily_tmin_f: pd.Series,
    daily_tmax_f: pd.Series,
    start: pd.Timestamp,
    base_f: float = DEFAULT_BASE_TEMP_F,
) -> pd.Series:
    """
    daily_tmin_f, daily_tmax_f: Series indexed by date.
    start: accumulation start (use the chill-requirement-met date from
        models.chill for a bloom-date prediction).
    """
    gdd = pd.Series(
        [
            daily_gdd(tmin, tmax, base_f)
            for tmin, tmax in zip(daily_tmin_f, daily_tmax_f)
        ],
        index=daily_tmin_f.index,
    )
    gdd.loc[gdd.index < start] = 0.0
    return gdd.cumsum()
