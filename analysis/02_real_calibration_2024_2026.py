"""
REAL DATA calibration -- checks the chill/GDD models against what actually
happened in 2024 (good harvest) and 2026 (total crop failure), using real
CIMIS station 262 (Linden) data pulled via ingestion/cimis_client.py.

Nothing here is synthetic. This is the actual test of whether the models
built in models/ line up with the farm's real outcomes.

Run:
    ./venv/bin/python analysis/02_real_calibration_2024_2026.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from models.chill import chill_requirement_met_date, SWEET_CHERRY_CHILL_HOURS_REQUIRED

HOURLY_PATH = REPO_ROOT / "data" / "climate" / "cimis_lodi_hourly.csv"
DAILY_PATH = REPO_ROOT / "data" / "climate" / "cimis_lodi_daily.csv"

FROST_THRESHOLD_F = 32.0
HEAT_THRESHOLD_F = 95.0
RAIN_CRACKING_THRESHOLD_IN = 1.1  # literature figure, ~28 L/m^2


def load():
    hourly = pd.read_csv(HOURLY_PATH, parse_dates=["timestamp"]).set_index("timestamp")
    daily = pd.read_csv(DAILY_PATH, parse_dates=["date"]).set_index("date")
    return hourly, daily


def chill_and_frost_check(hourly: pd.DataFrame, chill_start: str, window_start: str, window_end: str, label: str):
    print(f"--- {label} ---")
    temps = hourly.loc[chill_start:window_end, "hly_air_tmp"]
    met = chill_requirement_met_date(temps, start=pd.Timestamp(chill_start))
    print(f"Chill requirement ({SWEET_CHERRY_CHILL_HOURS_REQUIRED}h) met: {met}")

    window = hourly.loc[window_start:window_end, "hly_air_tmp"]
    freezing = window[window <= FROST_THRESHOLD_F]
    print(f"Hours <= {FROST_THRESHOLD_F}F in {window_start}..{window_end}: {len(freezing)}")
    if len(freezing):
        print("  Coldest reading per day:")
        print(freezing.groupby(freezing.index.date).min().to_string())
    print()


def heat_and_rain_check(daily: pd.DataFrame, start: str, end: str, label: str):
    print(f"--- {label} ---")
    window = daily.loc[start:end]
    hot_days = window[window["day_air_tmp_max"] >= HEAT_THRESHOLD_F]
    print(f"Days >= {HEAT_THRESHOLD_F}F: {len(hot_days)}")
    if len(hot_days):
        print(hot_days[["day_air_tmp_max"]].to_string())

    total_rain = window["day_precip"].sum()
    print(f"Total precip {start}..{end}: {total_rain:.2f} in")
    if total_rain >= RAIN_CRACKING_THRESHOLD_IN:
        print(
            f"  >= {RAIN_CRACKING_THRESHOLD_IN} in literature rain-cracking threshold -- "
            "flagged as a candidate driver if this window overlaps pre-harvest."
        )
    print()


def main():
    hourly, daily = load()

    print("=" * 70)
    print("2024 -- good harvest (30,514 lbs). Reported bloom: January 2024.")
    print("=" * 70)
    chill_and_frost_check(
        hourly, chill_start="2023-11-01", window_start="2024-01-01", window_end="2024-02-29",
        label="Chill accumulation + frost check, Jan-Feb 2024",
    )
    heat_and_rain_check(daily, "2024-04-01", "2024-05-31", "Heat/rain check, pre-harvest Apr-May 2024")

    print("=" * 70)
    print("2026 -- total crop failure (0 yield). Cause reported: frost and/or heat.")
    print("=" * 70)
    chill_and_frost_check(
        hourly, chill_start="2025-11-01", window_start="2026-02-01", window_end="2026-03-31",
        label="Chill accumulation + frost check, likely bloom window Feb-Mar 2026",
    )
    heat_and_rain_check(daily, "2026-04-01", "2026-07-31", "Heat/rain check, Apr-Jul 2026")

    print("=" * 70)
    print("INTERPRETATION (see data/yield/yield_history.csv for status):")
    print("=" * 70)
    print(
        "2024: model puts chill-met at Feb 13, after the reported January\n"
        "bloom -- and January 2024 had real hard freezes (down to 25.5F)\n"
        "that would have been severe if bloom were truly underway then.\n"
        "This suggests the reported bloom month is approximate and bloom\n"
        "more likely started after mid-February.\n\n"
        "2026: chill was satisfied earlier (Jan 26) than in 2024, so chill\n"
        "sufficiency isn't the failure driver. A real frost event Feb 20-21\n"
        "(29.2F) is the clearest candidate if bloom had started by then.\n"
        "Notable heat (>=95F) shows up in June-July, well after a typical\n"
        "May harvest window, so it's a weaker fit unless the season's\n"
        "timing shifted significantly. Confirm against real observation."
    )


if __name__ == "__main__":
    main()
