"""
Pulls REAL weather data for the Lodi-area station from CIMIS (California
Irrigation Management Information System -- the CA Dept. of Water
Resources' public ag weather network, https://cimis.water.ca.gov/).

Not runnable until CIMIS_API_KEY and CIMIS_STATION_ID are set (copy
.env.example to .env and fill them in -- see that file for how to get a
free key and data/climate/README.md for why station 262 (Linden) was
chosen).

Endpoint and parameter names below are the confirmed-live CIMIS StationWeb
API (verified via a real request that returned a proper subscription-key
auth error, not a 404, so the shape is correct -- only the exact response
JSON field names are unverified until a real key is available to test
against; fetch_daily/fetch_hourly save the raw JSON alongside the parsed
CSV specifically so that can be checked and the parser adjusted if needed).

Usage:
    ./venv/bin/python ingestion/cimis_client.py daily 2023-11-01 2024-06-01
    ./venv/bin/python ingestion/cimis_client.py hourly 2023-11-01 2024-06-01
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")

BASE_URL = "https://et.water.ca.gov/StationWeb/GetDataByStationNumber"

DAILY_ITEMS = [
    "day-air-tmp-avg",
    "day-air-tmp-max",
    "day-air-tmp-min",
    "day-dew-pnt",
    "day-asce-eto",
    "day-precip",
    "day-rel-hum-avg",
    "day-rel-hum-max",
    "day-rel-hum-min",
    "day-wind-spd-avg",
]

# hly-air-tmp is what models.chill wants directly -- real hourly readings,
# no sine-curve interpolation needed when this is available.
HOURLY_ITEMS = [
    "hly-air-tmp",
    "hly-precip",
    "hly-rel-hum",
    "hly-eto",
]

RAW_DIR = REPO_ROOT / "data" / "climate" / "raw_json"
OUTPUT_DAILY = REPO_ROOT / "data" / "climate" / "cimis_lodi_daily.csv"
OUTPUT_HOURLY = REPO_ROOT / "data" / "climate" / "cimis_lodi_hourly.csv"


def _get_credentials() -> tuple[str, str]:
    api_key = os.environ.get("CIMIS_API_KEY")
    station_id = os.environ.get("CIMIS_STATION_ID")
    if not api_key or not station_id:
        raise SystemExit(
            "CIMIS_API_KEY and CIMIS_STATION_ID must be set in .env "
            "(see .env.example) before this can run."
        )
    return api_key, station_id


def _fetch(start_date: str, end_date: str, is_hourly: bool, data_items: list[str]) -> dict:
    api_key, station_id = _get_credentials()
    params = {
        "stationNbrs": station_id,
        "startDate": start_date,
        "endDate": end_date,
        "isHourly": "true" if is_hourly else "false",
        "unitOfMeasure": "E",  # English units: F, inches, mph
        "dataItems": ",".join(data_items),
        "appKey": api_key,
    }
    resp = requests.get(BASE_URL, params=params, timeout=60)
    resp.raise_for_status()
    return resp.json()


def _save_raw(payload: dict, label: str) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / f"{label}.json"
    path.write_text(json.dumps(payload, indent=2))
    return path


def _extract_records(payload: dict) -> list[dict]:
    """
    Best-effort extraction of the per-timestamp records from the response.
    CIMIS's own docs describe a Data.Providers[].Records[] shape (same
    family as the older /api/data endpoint); this walks defensively in
    case StationWeb's shape differs, and always keeps the raw JSON (see
    _save_raw) so this can be corrected against a real response.
    """
    node = payload
    for key in ("Data", "Providers"):
        if isinstance(node, dict) and key in node:
            node = node[key]
    if isinstance(node, list) and node and "Records" in node[0]:
        records = []
        for provider in node:
            records.extend(provider.get("Records", []))
        return records
    # Fallback: maybe the payload IS already a flat list of records
    if isinstance(payload, list):
        return payload
    raise ValueError(
        "Unrecognized CIMIS response shape -- check the saved raw JSON "
        f"in {RAW_DIR} and update _extract_records()."
    )


def _flatten_record(record: dict, data_items: list[str]) -> dict:
    row = {"date": record.get("Date"), "hour": record.get("Hour")}
    for item in data_items:
        field = record.get(item)
        row[item.replace("-", "_")] = field.get("Value") if isinstance(field, dict) else field
    return row


def fetch_daily(start_date: str, end_date: str) -> pd.DataFrame:
    payload = _fetch(start_date, end_date, is_hourly=False, data_items=DAILY_ITEMS)
    _save_raw(payload, f"daily_{start_date}_{end_date}")
    records = _extract_records(payload)
    df = pd.DataFrame([_flatten_record(r, DAILY_ITEMS) for r in records])
    df["date"] = pd.to_datetime(df["date"])
    return df


def fetch_hourly(start_date: str, end_date: str) -> pd.DataFrame:
    payload = _fetch(start_date, end_date, is_hourly=True, data_items=HOURLY_ITEMS)
    _save_raw(payload, f"hourly_{start_date}_{end_date}")
    records = _extract_records(payload)
    df = pd.DataFrame([_flatten_record(r, HOURLY_ITEMS) for r in records])
    df["timestamp"] = pd.to_datetime(df["date"]) + pd.to_timedelta(
        df["hour"].astype(float), unit="h"
    )
    return df.drop(columns=["date", "hour"])


def _merge_and_save(df: pd.DataFrame, path: Path, dedup_cols: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = pd.read_csv(path, parse_dates=[c for c in dedup_cols])
        df = pd.concat([existing, df]).drop_duplicates(subset=dedup_cols)
    df = df.sort_values(dedup_cols)
    df.to_csv(path, index=False)
    print(f"Wrote {len(df)} rows to {path}")


def main() -> None:
    if len(sys.argv) != 4 or sys.argv[1] not in ("daily", "hourly"):
        raise SystemExit(
            "Usage: cimis_client.py <daily|hourly> <start_date YYYY-MM-DD> <end_date YYYY-MM-DD>"
        )
    mode, start_date, end_date = sys.argv[1], sys.argv[2], sys.argv[3]
    if mode == "daily":
        df = fetch_daily(start_date, end_date)
        _merge_and_save(df, OUTPUT_DAILY, dedup_cols=["date"])
    else:
        df = fetch_hourly(start_date, end_date)
        _merge_and_save(df, OUTPUT_HOURLY, dedup_cols=["timestamp"])


if __name__ == "__main__":
    main()
