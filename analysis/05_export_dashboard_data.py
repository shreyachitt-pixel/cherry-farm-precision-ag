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
import sys
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


def uncertainty_propagation_summary() -> dict:
    # Hand-cited from a real run of analysis/07_uncertainty_propagation.py
    # (2000 Monte Carlo trials, real 2024 CIMIS data) -- re-run that
    # script to reproduce/verify.
    return {
        "n_trials": 2000,
        "chill_met_date_deterministic": "2024-02-13",
        "chill_met_offset_days": {"median": 0.1, "p5": -1.9, "p95": 9.1},
        "chill_met_note": "Distribution is genuinely multimodal (clustered at a few discrete "
                           "offsets), not a smooth spread -- a handful of specific real days sit "
                           "right at the 45F chill threshold, so a small sensor bias flips whether "
                           "those particular days count.",
        "gdd_by_mar15": {"median": 429, "p5": 311, "p95": 439, "unit": "GDD-F"},
        "eto_on_apr15": {"median": 0.154, "p5": 0.088, "p95": 0.217, "unit": "in/day"},
    }


def chill_threshold_inference_summary() -> dict:
    # Hand-cited from a real run of analysis/08_chill_threshold_inference.py.
    return {
        "prior": {"mean": 750, "ci90_lo": 627, "ci90_hi": 873},
        "posterior": {"mean": 730, "std": 69, "ci90_lo": 616, "ci90_hi": 842},
        "width_ratio_pct": 92,
        "interpretation": "Posterior barely narrower than the prior -- correct behavior given how "
                           "weak two years of soft evidence really is. Not read as 'the threshold is "
                           "now known'; it's evidence two years isn't enough to move far past the "
                           "literature default.",
    }


def chill_portions_summary() -> list[dict]:
    # Hand-cited from a real run of analysis/09_chill_portions_real_data.py.
    return [
        {"year": 2024, "chill_hours": 861, "chill_portions": 67.7},
        {"year": 2026, "chill_hours": 1026, "chill_portions": 66.1},
    ]


def pre_registration_summary() -> dict:
    sys.path.insert(0, str(REPO_ROOT))
    from models.statistical_power import required_n_for_correlation, achieved_power_for_n

    power_table = [
        {"n": n, "power_r05": round(achieved_power_for_n(n, 0.5), 3), "power_r07": round(achieved_power_for_n(n, 0.7), 3)}
        for n in [5, 8, 10, 15, 20]
    ]
    return {
        "n_hypotheses": 4,
        "alpha_bonferroni": 0.0125,
        "minimum_n_gate": 8,
        "real_bearing_years_so_far": 2,
        "required_n_r05_80pct_power": round(required_n_for_correlation(0.5), 1),
        "required_n_r07_80pct_power": round(required_n_for_correlation(0.7), 1),
        "power_table": power_table,
        "hypotheses": [
            "H1: bloom-window frost exposure vs. yield",
            "H2: prior-summer heat (bud initiation) vs. next year's yield",
            "H3: pre-harvest rain vs. yield (cracking)",
            "H4: winter chill sufficiency vs. yield",
        ],
    }


def main() -> None:
    data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "yield_history": yield_history(),
        "sensor_completeness": sensor_completeness(),
        "calibration_findings": calibration_findings(),
        "uncertainty_propagation": uncertainty_propagation_summary(),
        "chill_threshold_inference": chill_threshold_inference_summary(),
        "chill_portions": chill_portions_summary(),
        "pre_registration": pre_registration_summary(),
        "cimis_station": {"id": 262, "name": "Linden", "county": "San Joaquin"},
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(data, indent=2))
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
