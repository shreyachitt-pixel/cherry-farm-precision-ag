"""
Runs the Dynamic Model (Chill Portions) against the real 2024 and 2026
CIMIS hourly data and compares its accumulation curve to the simple
chill-hours count already used elsewhere in this project.

No "chill met" date is reported here -- unlike models/chill.py, this
module doesn't have a cited required-portions threshold for sweet
cherry (see models/chill_portions.py's docstring for why). This script
shows what the Dynamic Model says about the SHAPE of accumulation --
in particular, whether it tells a meaningfully different story from
the simple hours count about when winter chill was actually
progressing fastest.

Run:
    ./venv/bin/python analysis/09_chill_portions_real_data.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from models.chill import cumulative_chill_hours
from models.chill_portions import dynamic_model_cumulative_portions

WINDOWS = {
    "2024": ("2023-11-01", "2024-03-01"),
    "2026": ("2025-11-01", "2026-03-01"),
}


def load_hourly() -> pd.Series:
    df = pd.read_csv(REPO_ROOT / "data" / "climate" / "cimis_lodi_hourly.csv", parse_dates=["timestamp"]).set_index("timestamp")
    return df["hly_air_tmp"].sort_index()


def fill_gaps_within_window(series: pd.Series) -> pd.Series:
    """Interpolates gaps WITHIN one continuous real-data window only --
    the two windows pulled for this project (2024, 2026) are ~17 months
    apart, and naively reindexing across that whole span would invent 17
    months of fake interpolated data neither window actually needs."""
    full_index = pd.date_range(series.index.min(), series.index.max(), freq="h")
    gaps = full_index.difference(series.index)
    if len(gaps):
        print(f"  Note: {len(gaps)} gap hour(s) within this window, filled by linear interpolation "
              "(the Dynamic Model is a genuine recurrence and can't skip hours the way the simple count can).")
        return series.reindex(full_index).interpolate()
    return series


def main():
    hourly = load_hourly()
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    for ax, (label, (start, end)) in zip(axes, WINDOWS.items()):
        print(f"=== {label} ===")
        window = fill_gaps_within_window(hourly.loc[start:end])
        chill_hours = cumulative_chill_hours(window, start=pd.Timestamp(start))
        chill_portions = dynamic_model_cumulative_portions(window)

        # Two different units/scales -- plot on separate axes on the SAME
        # chart is a dual-axis chart, which is misleading (arbitrary
        # relative scaling invents an apparent correlation). Instead,
        # normalize each to its own final value so the shapes of the two
        # accumulation CURVES are directly comparable -- that's the real
        # question here (does one model say chill progressed faster/
        # slower at different points than the other), not their absolute
        # units side by side.
        ax.plot(window.index, chill_hours / chill_hours.iloc[-1], label="Chill hours (normalized)")
        ax.plot(window.index, chill_portions / chill_portions.iloc[-1], label="Chill portions (Dynamic Model, normalized)")
        ax.set_title(f"{label}: accumulation shape comparison")
        ax.set_ylabel("Fraction of period total")
        ax.legend()
        ax.tick_params(axis="x", rotation=30)

        print(f"  Final chill hours: {chill_hours.iloc[-1]:.0f}h")
        print(f"  Final chill portions: {chill_portions.iloc[-1]:.1f} CP")

    fig.suptitle("Chill-hours count vs. Dynamic Model (Chill Portions) -- real CIMIS data, station 262")
    fig.tight_layout()
    out_path = REPO_ROOT / "visualizations" / "06_chill_portions_vs_hours.png"
    fig.savefig(out_path, dpi=130)
    print(f"\nSaved {out_path}")


if __name__ == "__main__":
    main()
