"""
Exports real project data as JSON for the static dashboard (site/) to
fetch client-side. GitHub Pages is static hosting -- it can't run Python
-- so this script is the bridge: run it, commit the output, the page
reads the committed JSON. Nothing in the output is synthetic.

Run:
    ./venv/bin/python analysis/05_export_dashboard_data.py
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = REPO_ROOT / "site" / "data" / "dashboard.json"

SENSOR_COLS = ["soil_moisture_1", "soil_moisture_2", "air_temp", "humidity", "soil_temp", "light_lux"]


def yield_history() -> list[dict]:
    df = pd.read_csv(REPO_ROOT / "data" / "yield" / "yield_history.csv")
    rows = []
    for _, r in df.iterrows():
        year = int(r["year"])
        lbs = r["total_yield_lbs_delivered"]
        if pd.isna(lbs):
            status, lbs_out = "pending", None
        elif lbs == 0 and year <= 2023:
            status, lbs_out = "pre-bearing", 0
        elif lbs == 0:
            status, lbs_out = "failure", 0
        else:
            status, lbs_out = "harvested", int(lbs)
        rows.append({"year": year, "lbs_delivered": lbs_out, "status": status})
    return rows


def sensor_completeness() -> dict:
    df = pd.read_csv(REPO_ROOT / "data" / "raw" / "sensordata.csv", parse_dates=["timestamp"])
    total = len(df)
    per_col = {col: round(100 * df[col].notna().sum() / total, 1) for col in SENSOR_COLS}
    stations = (
        df.groupby("station")["timestamp"]
        .agg(["min", "max", "count"])
        .reset_index()
        .to_dict(orient="records")
    )
    for s in stations:
        s["min"] = str(s["min"])
        s["max"] = str(s["max"])
    return {
        "total_readings": int(total),
        "date_range": [str(df["timestamp"].min()), str(df["timestamp"].max())],
        "per_column_pct": per_col,
        "stations": stations,
    }


def calibration_findings() -> list[dict]:
    # Hand-curated summary of analysis/02_real_calibration_2024_2026.py's
    # real output -- re-run that script to reproduce/verify these numbers.
    return [
        {
            "year": 2024,
            "outcome": "30,514 lbs delivered (good harvest)",
            "chill_met": "2024-02-13",
            "reported_bloom": "January 2024 (approximate)",
            "finding": "Model-predicted dormancy break (Feb 13) is after the reported bloom month. "
                       "January 2024 had real hard freezes (down to 25.5F) that would likely have "
                       "damaged an active bloom -- suggesting true bloom was later than reported, "
                       "consistent with the good outcome.",
        },
        {
            "year": 2026,
            "outcome": "0 lbs -- total crop failure",
            "chill_met": "2026-01-26",
            "reported_bloom": "Not precisely recorded",
            "finding": "Chill was satisfied earlier than 2024, so chill sufficiency isn't the driver. "
                       "A real frost event Feb 20-21, 2026 (29.2F) is the leading candidate. Real heat "
                       "(up to 100.3F) also shows up June-July, within the literature-documented "
                       "flower-bud-initiation window for the 2027 crop.",
        },
    ]


def main() -> None:
    data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "yield_history": yield_history(),
        "sensor_completeness": sensor_completeness(),
        "calibration_findings": calibration_findings(),
        "cimis_station": {"id": 262, "name": "Linden", "county": "San Joaquin"},
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(data, indent=2))
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
