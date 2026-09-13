"""
Pulls REAL short-range hourly weather forecast (~7 days out) from the
National Weather Service's free public API (api.weather.gov) -- no API
key needed. This is the forecast leg of frost alerting: CIMIS (see
cimis_client.py) only publishes observed/historical station data, not
forecasts, so it can't warn you before a frost night, only confirm one
happened after the fact.

Uses the farm's approximate location (Lodi, CA -- not the exact street
address, consistent with this project's data-provenance rules) to look
up the correct NWS forecast grid, then pulls the hourly forecast.

Usage:
    ./venv/bin/python ingestion/nws_forecast.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import requests

REPO_ROOT = Path(__file__).resolve().parent.parent

# Approximate farm location (Lodi, CA) -- matches LODI_LATITUDE in
# models/eto.py. Not the exact street address.
FARM_LAT = 38.14
FARM_LON = -121.27

USER_AGENT = "cherry-farm-precision-ag (student research project, contact via github)"

OUTPUT_PATH = REPO_ROOT / "data" / "climate" / "nws_hourly_forecast.csv"


def _get(url: str) -> dict:
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_forecast_grid_url() -> str:
    points = _get(f"https://api.weather.gov/points/{FARM_LAT},{FARM_LON}")
    return points["properties"]["forecastHourly"]


def fetch_hourly_forecast() -> pd.DataFrame:
    grid_url = get_forecast_grid_url()
    data = _get(grid_url)
    periods = data["properties"]["periods"]
    df = pd.DataFrame(
        [
            {
                "timestamp": p["startTime"],
                "temp_f": p["temperature"],
                "short_forecast": p["shortForecast"],
                "wind_speed": p["windSpeed"],
                "relative_humidity_pct": (p.get("relativeHumidity") or {}).get("value"),
            }
            for p in periods
        ]
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def main() -> None:
    df = fetch_hourly_forecast()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"Wrote {len(df)} hourly forecast rows ({df['timestamp'].min()} to {df['timestamp'].max()}) to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
