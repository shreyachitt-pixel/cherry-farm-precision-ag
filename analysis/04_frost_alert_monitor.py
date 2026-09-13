"""
Frost-alert monitor: pulls the real ~7-day NWS forecast for the farm and
flags any hour that crosses the frost-damage thresholds for the current
(or specified) bud stage.

This is the actionable piece the rest of the project builds toward --
models/chill.py and models/gdd.py explain and predict; this is the one
that's meant to be run regularly during frost season (roughly
January-April) and actually change what happens that night.

Bud stage: pass --stage explicitly once you've visually checked the buds
(the whole point of the two-tier WATCH/WARNING system is that a dormant
bud and an open flower need completely different responses to the same
26F night). Without --stage, this defaults to the conservative
"full_bloom" assumption during frost season, or "dormant_swollen_bud"
outside it -- see models/frost_risk.py for the full stage table.

Usage:
    ./venv/bin/python analysis/04_frost_alert_monitor.py
    ./venv/bin/python analysis/04_frost_alert_monitor.py --stage open_cluster
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from ingestion.nws_forecast import fetch_hourly_forecast
from models.frost_risk import (
    assess_frost_risk,
    DEFAULT_STAGE_AFTER_CHILL_MET,
    DEFAULT_STAGE_BEFORE_CHILL_MET,
    STAGE_ORDER,
)

# Frost season for this orchard: chill is typically satisfied by late
# Jan (see analysis/02_real_calibration_2024_2026.py), and by ~mid-April
# fruit is generally past the most sensitive stages. Outside this window
# the conservative default assumption is dormancy.
FROST_SEASON_START_MONTH_DAY = (1, 15)
FROST_SEASON_END_MONTH_DAY = (4, 15)


def default_stage(as_of: pd.Timestamp) -> str:
    as_of = as_of.tz_localize(None) if as_of.tzinfo is not None else as_of
    season_start = pd.Timestamp(year=as_of.year, month=FROST_SEASON_START_MONTH_DAY[0], day=FROST_SEASON_START_MONTH_DAY[1])
    season_end = pd.Timestamp(year=as_of.year, month=FROST_SEASON_END_MONTH_DAY[0], day=FROST_SEASON_END_MONTH_DAY[1])
    if season_start <= as_of <= season_end:
        return DEFAULT_STAGE_AFTER_CHILL_MET
    return DEFAULT_STAGE_BEFORE_CHILL_MET


def run(stage: str | None) -> int:
    print("Fetching real NWS hourly forecast for the farm (Lodi, CA area)...")
    forecast = fetch_hourly_forecast()
    now = pd.Timestamp.now(tz=forecast["timestamp"].dt.tz)

    chosen_stage = stage or default_stage(now)
    print(f"Bud stage assumed for this run: {chosen_stage}"
          + ("" if stage else "  (auto-selected by calendar date -- pass --stage to override)"))
    print(f"Forecast window: {forecast['timestamp'].min()} to {forecast['timestamp'].max()}\n")

    alerts = []
    for _, row in forecast.iterrows():
        result = assess_frost_risk(row["temp_f"], chosen_stage)
        if result.level != "none":
            alerts.append((row["timestamp"], row["temp_f"], result))

    if not alerts:
        print(f"No frost WATCH or WARNING hours in the forecast window at stage '{chosen_stage}'.")
        return 0

    print(f"{len(alerts)} hour(s) flagged:\n")
    for ts, temp, result in alerts:
        marker = "WARNING" if result.level == "warning" else "WATCH  "
        print(
            f"  [{marker}] {ts:%Y-%m-%d %H:%M} -- forecast {temp}F "
            f"(10% kill @ {result.temp_10pct_kill_f}F, 90% kill @ {result.temp_90pct_kill_f}F, stage={chosen_stage})"
        )

    warning_count = sum(1 for _, _, r in alerts if r.level == "warning")
    if warning_count:
        print(
            f"\n{warning_count} WARNING-level hour(s) -- at/below the 90%-bud-kill threshold "
            f"for '{chosen_stage}'. This is when frost protection (overhead sprinklers, wind "
            "machines -- see analysis/2027_outlook.md) should actually be deployed, not just watched."
        )
    return 1 if warning_count else 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stage", choices=STAGE_ORDER, default=None,
        help="Current bud development stage (visually confirmed). Defaults to a calendar-based guess.",
    )
    args = parser.parse_args()
    sys.exit(run(args.stage))


if __name__ == "__main__":
    main()
