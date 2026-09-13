"""
SYNTHETIC DATA DEMO — proves the chill/GDD/irrigation pipeline runs
end-to-end, using data/simulated/SYNTHETIC_lodi_climate.csv (fabricated).

This does NOT produce a real finding about the farm. It exists to validate
the pipeline shape before real CIMIS + sensor data replace the inputs.
Every number this script prints describes the synthetic data, not Lodi or
the farm.

Run:
    ./venv/bin/python analysis/00_synthetic_pipeline_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from models.chill import cumulative_chill_hours, chill_requirement_met_date, SWEET_CHERRY_CHILL_HOURS_REQUIRED
from models.gdd import cumulative_gdd
from models.eto import hargreaves_eto_in
from models.irrigation import etc_inches, net_irrigation_in, drip_runtime_hours, kc_for_days_since_bloom

CLIMATE_PATH = REPO_ROOT / "data" / "simulated" / "SYNTHETIC_lodi_climate.csv"
LODI_LATITUDE = 38.13
CHILL_SEASON_START = pd.Timestamp("2025-11-01")


def load_synthetic_climate() -> pd.DataFrame:
    if not CLIMATE_PATH.exists():
        raise SystemExit(
            f"{CLIMATE_PATH} not found — run generate_synthetic_climate.py first"
        )
    df = pd.read_csv(CLIMATE_PATH, parse_dates=["timestamp"]).set_index("timestamp")
    return df


def main() -> None:
    print("*** SYNTHETIC DATA — pipeline validation only, not a real finding ***\n")
    df = load_synthetic_climate()

    # 1. Chill accumulation
    hourly_temp = df["air_temp_f"]
    cum_chill = cumulative_chill_hours(hourly_temp, start=CHILL_SEASON_START)
    met_date = chill_requirement_met_date(hourly_temp, start=CHILL_SEASON_START)
    print(f"Chill requirement ({SWEET_CHERRY_CHILL_HOURS_REQUIRED}h) met on (synthetic data): {met_date}")

    if met_date is None:
        print("Chill requirement never met in this synthetic window — stopping demo.")
        return

    # 2. GDD accumulation from chill-met date -> bloom prediction
    daily = df.resample("D").agg(tmin=("air_temp_f", "min"), tmax=("air_temp_f", "max"))
    cum_gdd = cumulative_gdd(daily["tmin"], daily["tmax"], start=met_date.normalize())
    print(f"GDD accumulated by end of synthetic series: {cum_gdd.iloc[-1]:.0f} GDD-F")
    print(
        "  (Bloom-trigger GDD threshold isn't hardcoded here — it needs "
        "calibration against a real observed bloom date once the farm has one.)"
    )

    # 3. ETo/ETc/irrigation for a sample mid-season day
    sample_day = daily.index[len(daily) // 2]
    tmin, tmax = daily.loc[sample_day, ["tmin", "tmax"]]
    eto = hargreaves_eto_in(tmin_f=tmin, tmax_f=tmax, day_of_year=sample_day.dayofyear, latitude_deg=LODI_LATITUDE)
    days_since_bloom = 40  # illustrative
    kc = kc_for_days_since_bloom(days_since_bloom)
    etc = etc_inches(eto, kc)
    rain_that_day = df.loc[sample_day.strftime("%Y-%m-%d"), "precip_in"].sum()
    net_in = net_irrigation_in(etc, effective_rain_in=rain_that_day * 0.7)  # ~70% effective rainfall, typical rule of thumb
    hours = drip_runtime_hours(
        depth_in=net_in, wetted_area_sqft=25.0, emitters_per_tree=4, flow_gph_per_emitter=1.0
    )

    print(f"\nSample day {sample_day.date()} (synthetic):")
    print(f"  Tmin/Tmax: {tmin:.1f}F / {tmax:.1f}F")
    print(f"  ETo (Hargreaves): {eto:.3f} in/day")
    print(f"  Kc @ {days_since_bloom} days since bloom: {kc:.2f}")
    print(f"  ETc: {etc:.3f} in/day")
    print(f"  Rain that day: {rain_that_day:.3f} in")
    print(f"  Net irrigation needed: {net_in:.3f} in")
    print(f"  Drip runtime (4 emitters/tree, 1 gph, 25 sq ft wetted area): {hours:.2f} hours")


if __name__ == "__main__":
    main()
