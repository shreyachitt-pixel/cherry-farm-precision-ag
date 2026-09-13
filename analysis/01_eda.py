"""
Exploratory data analysis on the REAL sensor data (data/raw/sensordata.csv
only — no synthetic data touched here).

Run:
    ./venv/bin/python analysis/01_eda.py

Prints summary stats and writes time-series + coverage plots to
visualizations/.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = REPO_ROOT / "data" / "raw" / "sensordata.csv"
VIZ_DIR = REPO_ROOT / "visualizations"

SENSOR_COLS = [
    "soil_moisture_1",
    "soil_moisture_2",
    "air_temp",
    "humidity",
    "soil_temp",
    "light_lux",
]


def load() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH, parse_dates=["timestamp"])
    return df


def print_coverage_table(df: pd.DataFrame) -> None:
    print(f"Total real readings: {len(df)}")
    print(f"Date range: {df.timestamp.min()} to {df.timestamp.max()}")
    print()
    print("Per-station date range:")
    print(df.groupby("station").timestamp.agg(["min", "max", "count"]))
    print()
    print("Per-column coverage:")
    for col in SENSOR_COLS:
        n = df[col].notna().sum()
        pct = 100 * n / len(df)
        print(f"  {col:<18} {n:>4}/{len(df)}  ({pct:5.1f}%)")


def print_descriptive_stats(df: pd.DataFrame) -> None:
    print()
    print("Descriptive stats (present values only):")
    print(df[SENSOR_COLS].describe().round(2))


def plot_time_series(df: pd.DataFrame) -> None:
    VIZ_DIR.mkdir(exist_ok=True)
    fig, axes = plt.subplots(len(SENSOR_COLS), 1, figsize=(11, 2.2 * len(SENSOR_COLS)), sharex=True)
    for ax, col in zip(axes, SENSOR_COLS):
        for station, sub in df.groupby("station"):
            valid = sub.dropna(subset=[col])
            if len(valid):
                ax.plot(valid.timestamp, valid[col], marker=".", linestyle="-", markersize=3, label=station)
        ax.set_ylabel(col)
        ax.legend(loc="upper right", fontsize=8)
    axes[-1].set_xlabel("timestamp")
    fig.suptitle("Real sensor readings over time (gaps = sensor not yet wired in / not reporting)")
    fig.tight_layout()
    out = VIZ_DIR / "01_time_series.png"
    fig.savefig(out, dpi=130)
    print(f"\nSaved {out}")


def plot_coverage_bar(df: pd.DataFrame) -> None:
    coverage = {col: 100 * df[col].notna().sum() / len(df) for col in SENSOR_COLS}
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(coverage.keys(), coverage.values())
    ax.set_ylabel("% of readings with a value")
    ax.set_title("Real data completeness by sensor")
    ax.set_ylim(0, 100)
    plt.xticks(rotation=30, ha="right")
    fig.tight_layout()
    out = VIZ_DIR / "02_data_completeness.png"
    fig.savefig(out, dpi=130)
    print(f"Saved {out}")


def main() -> None:
    df = load()
    print_coverage_table(df)
    print_descriptive_stats(df)
    plot_time_series(df)
    plot_coverage_bar(df)


if __name__ == "__main__":
    main()
