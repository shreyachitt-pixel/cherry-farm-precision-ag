"""
Simulates an hourly temperature curve from daily min/max — needed because
CIMIS's standard daily data gives day-air-tmp-max/min/avg, not an
hour-by-hour series, but models.chill needs hourly readings to count
chill hours.

This is a standard technique in phenology modeling (a "single sine curve"
method): assume Tmin occurs near dawn (~5am) and Tmax in mid-afternoon
(~2pm), and interpolate sinusoidally between them, using the previous/next
day's values to shape the approach to each day's Tmin. It's an
approximation, not a measurement — real hourly CIMIS data (if pulled via
the station's hourly data items) should be preferred over this when
available.
"""

from __future__ import annotations

import math

import pandas as pd

TMIN_HOUR = 5
TMAX_HOUR = 14


def _hour_temp(hour: int, tmin_today: float, tmax_today: float, tmin_tomorrow: float) -> float:
    """Temperature at a given hour of one day via sine interpolation
    between the day's Tmin/Tmax, tapering toward tomorrow's Tmin overnight."""
    if TMIN_HOUR <= hour <= TMAX_HOUR:
        # Rising/warming half of the day: Tmin at 5am -> Tmax at 2pm
        frac = (hour - TMIN_HOUR) / (TMAX_HOUR - TMIN_HOUR)
        return tmin_today + (tmax_today - tmin_today) * math.sin(frac * math.pi / 2)
    else:
        # Cooling half: Tmax at 2pm -> tomorrow's Tmin at 5am next day
        if hour > TMAX_HOUR:
            hours_since_max = hour - TMAX_HOUR
        else:  # hour < TMIN_HOUR, i.e. past midnight before today's Tmin
            hours_since_max = (24 - TMAX_HOUR) + hour
        total_cooling_hours = (24 - TMAX_HOUR) + TMIN_HOUR
        frac = hours_since_max / total_cooling_hours
        return tmax_today - (tmax_today - tmin_tomorrow) * math.sin(frac * math.pi / 2)


def simulate_hourly_temps(daily_tmin: pd.Series, daily_tmax: pd.Series) -> pd.Series:
    """
    daily_tmin, daily_tmax: Series indexed by date (one value per day).
    Returns an hourly Series over the same date range (last day repeats its
    own Tmin as the "tomorrow" value, since there's nothing to taper to).
    """
    dates = daily_tmin.index
    records = {}
    for i, date in enumerate(dates):
        tmin_today = daily_tmin.iloc[i]
        tmax_today = daily_tmax.iloc[i]
        tmin_tomorrow = daily_tmin.iloc[i + 1] if i + 1 < len(dates) else tmin_today
        for hour in range(24):
            ts = pd.Timestamp(date) + pd.Timedelta(hours=hour)
            records[ts] = _hour_temp(hour, tmin_today, tmax_today, tmin_tomorrow)
    return pd.Series(records).sort_index()
