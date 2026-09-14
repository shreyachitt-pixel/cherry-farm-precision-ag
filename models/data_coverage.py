"""
Checks whether a time-indexed real dataset actually covers a date
window, rather than trusting a plain pandas .loc[start:end] slice to be
empty when data is missing. That trust is misplaced whenever the
underlying index has data from some OTHER, unrelated period: an
unbounded or mismatched slice can silently return real rows from the
wrong window instead of correctly reporting "no data here" -- exactly
the bug this module exists to prevent (found and fixed while building
analysis/10_populate_hypothesis_tracking_log.py, where several years
without real climate data were silently computing values from a much
later, unrelated real data window).
"""

from __future__ import annotations

import pandas as pd


def has_adequate_coverage(
    index: pd.DatetimeIndex,
    start: pd.Timestamp,
    end: pd.Timestamp,
    expected_per_day: int,
    min_fraction: float = 0.9,
) -> bool:
    """True only if at least `min_fraction` of the expected number of
    readings for [start, end] actually fall inside that window."""
    in_window = index[(index >= start) & (index <= end)]
    expected = max((end - start).days * expected_per_day, 1)
    return len(in_window) >= min_fraction * expected
