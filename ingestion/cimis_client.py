"""
Pulls REAL historical/daily weather data for the Lodi station from CIMIS
(California Irrigation Management Information System — the CA Dept. of
Water Resources' public ag weather network, https://cimis.water.ca.gov/).

Not runnable until CIMIS_API_KEY and CIMIS_STATION_ID are set (copy
.env.example to .env and fill them in — see that file for how to get a
free key and find the nearest station number).

This targets the documented CIMIS WSN "data" API shape (appKey, targets,
startDate, endDate, dataItems as query params, JSON response). Re-check
against the current API docs at signup time in case the contract has
changed since this was written.

Usage:
    ./venv/bin/python ingestion/cimis_client.py 2026-01-01 2026-01-31
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")

CIMIS_DATA_URL = "https://et.water.ca.gov/api/data"

DATA_ITEMS = [
    "day-air-tmp-max",
    "day-air-tmp-min",
    "day-air-tmp-avg",
    "day-rel-hum-max",
    "day-rel-hum-min",
    "day-rel-hum-avg",
    "day-precip",
    "day-wind-spd-avg",
    "day-eto",
]

OUTPUT_PATH = REPO_ROOT / "data" / "climate" / "cimis_lodi_daily.csv"


def fetch_daily(start_date: str, end_date: str) -> pd.DataFrame:
    api_key = os.environ.get("CIMIS_API_KEY")
    station_id = os.environ.get("CIMIS_STATION_ID")
    if not api_key or not station_id:
        raise SystemExit(
            "CIMIS_API_KEY and CIMIS_STATION_ID must be set in .env "
            "(see .env.example) before this can run."
        )

    params = {
        "appKey": api_key,
        "targets": station_id,
        "startDate": start_date,
        "endDate": end_date,
        "dataItems": ",".join(DATA_ITEMS),
        "unitOfMeasure": "E",  # English units (F, inches, mph)
    }
    resp = requests.get(CIMIS_DATA_URL, params=params, timeout=30)
    resp.raise_for_status()
    payload = resp.json()

    records = []
    for record in payload["Data"]["Providers"][0]["Records"]:
        row = {"date": record["Date"]}
        for item in DATA_ITEMS:
            key = item.replace("day-", "").replace("-", "_")
            field = record.get(item.replace("day-", "Day").replace("-", ""))
            # CIMIS field naming varies by exact API version — fall back to
            # scanning known keys if the direct mapping doesn't match.
            row[key] = field["Value"] if isinstance(field, dict) else None
        records.append(row)

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    return df


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: cimis_client.py <start_date YYYY-MM-DD> <end_date YYYY-MM-DD>")
    start_date, end_date = sys.argv[1], sys.argv[2]
    df = fetch_daily(start_date, end_date)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    if OUTPUT_PATH.exists():
        existing = pd.read_csv(OUTPUT_PATH, parse_dates=["date"])
        df = pd.concat([existing, df]).drop_duplicates(subset=["date"]).sort_values("date")
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"Wrote {len(df)} real CIMIS rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
