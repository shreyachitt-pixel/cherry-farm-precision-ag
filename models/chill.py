"""
Winter chill accumulation for dormancy break.

Uses the simple "chill hours" model: count hours where air temperature is
between a lower and upper bound (classically 32-45F, sometimes stated as
"below 45F" with no lower bound). Sweet cherry needs roughly 700-800 chill
hours to reliably break dormancy (UC Davis Fruit & Nut Research and
Information Center; some varieties range 350-1200h), accumulated from
around Nov 1 in the Central Valley.

This is the simple, well-documented model — not the more accurate but more
complex Dynamic Model (Chill Portions), which is a reasonable next step
once there's a full season of real hourly data to validate against.
"""

from __future__ import annotations

import pandas as pd

DEFAULT_UPPER_BOUND_F = 45.0
DEFAULT_LOWER_BOUND_F = 32.0
SWEET_CHERRY_CHILL_HOURS_REQUIRED = 750  # midpoint of the commonly cited 700-800h range


def is_chill_hour(
    temp_f: float,
    upper_bound_f: float = DEFAULT_UPPER_BOUND_F,
    lower_bound_f: float | None = DEFAULT_LOWER_BOUND_F,
) -> bool:
    if temp_f > upper_bound_f:
        return False
    if lower_bound_f is not None and temp_f < lower_bound_f:
        return False
    return True


def cumulative_chill_hours(
    hourly_temp_f: pd.Series,
    start: pd.Timestamp,
    upper_bound_f: float = DEFAULT_UPPER_BOUND_F,
    lower_bound_f: float | None = DEFAULT_LOWER_BOUND_F,
) -> pd.Series:
    """
    hourly_temp_f: Series of air temp (F) indexed by hourly timestamp.
    start: accumulation start date (chill season conventionally starts
        ~Nov 1 in the Central Valley).
    Returns a cumulative chill-hour count indexed the same way, zero before
    `start`.
    """
    is_chill = hourly_temp_f.apply(
        lambda t: is_chill_hour(t, upper_bound_f, lower_bound_f)
    ).astype(int)
    is_chill.loc[hourly_temp_f.index < start] = 0
    return is_chill.cumsum()


def chill_requirement_met_date(
    hourly_temp_f: pd.Series,
    start: pd.Timestamp,
    required_hours: int = SWEET_CHERRY_CHILL_HOURS_REQUIRED,
    upper_bound_f: float = DEFAULT_UPPER_BOUND_F,
    lower_bound_f: float | None = DEFAULT_LOWER_BOUND_F,
) -> pd.Timestamp | None:
    """First timestamp at which cumulative chill hours reach the
    requirement, or None if never reached in the given series."""
    cum = cumulative_chill_hours(hourly_temp_f, start, upper_bound_f, lower_bound_f)
    met = cum[cum >= required_hours]
    return met.index[0] if len(met) else None
