"""
SYNTHETIC DATA -- irrigation trigger dry run. Not a real finding about the farm.

Runs a soil-moisture-driven irrigation trigger on
data/simulated/SYNTHETIC_farm_sensors.csv. Two parts:

  1. Trigger: fires when the 6-hour mean of BOTH soil moisture channels is
     drier (higher raw ADC on a capacitive sensor) than a threshold. The
     threshold is a PLACEHOLDER = real farm mean + 1 std, because no gravimetric
     calibration exists yet (data/calibration/). It is not agronomically valid.
  2. Dose: on trigger days, converts Hargreaves ETo x Kc into drip runtime via
     models.irrigation (Kc = post-harvest 0.75, since the bloom date for the
     season is not on file).

Run:
    ./venv/bin/python analysis/11_irrigation_trigger_synthetic.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from models.eto import hargreaves_eto_in
from models.irrigation import STAGE_KC, etc_inches, net_irrigation_in, drip_runtime_hours

LODI_LATITUDE = 38.13
KC = STAGE_KC[-1][1]
DRIP = dict(wetted_area_sqft=25, emitters_per_tree=4, flow_gph_per_emitter=1)

real = pd.read_csv(REPO_ROOT / "data" / "raw" / "sensordata.csv")
ok = real[real.soil_moisture_2 > 2500]  # exclude the 2 suspect sensor-2 reads
THRESH = {c: ok[c].mean() + ok[c].std() for c in ("soil_moisture_1", "soil_moisture_2")}

df = pd.read_csv(REPO_ROOT / "data" / "simulated" / "SYNTHETIC_farm_sensors.csv",
                 parse_dates=["timestamp"]).set_index("timestamp")
print("*** SYNTHETIC DATA -- dry run, not a real finding ***")
print(f"Placeholder dry thresholds (raw ADC): { {k: round(v) for k, v in THRESH.items()} }\n")

sm = df[list(THRESH)].rolling(12, min_periods=12).mean()  # 12 x 30 min = 6 h
dry = (sm.soil_moisture_1 > THRESH["soil_moisture_1"]) & (sm.soil_moisture_2 > THRESH["soil_moisture_2"])
print(f"Readings: {len(df)}; trigger true in {int(dry.sum())} ({dry.mean():.1%})")

rows = []
for day, g in df.groupby(df.index.normalize()):
    tmin_f = g.air_temp.min() * 9 / 5 + 32
    tmax_f = g.air_temp.max() * 9 / 5 + 32
    eto = hargreaves_eto_in(tmin_f, tmax_f, day.dayofyear, LODI_LATITUDE)
    need = net_irrigation_in(etc_inches(eto, KC), 0.0)
    fired = bool(dry.reindex(g.index).any())
    rows.append((day.date(), round(tmin_f), round(tmax_f), round(eto, 3), round(need, 3),
                 fired, round(drip_runtime_hours(need, **DRIP), 2) if fired else 0.0))
out = pd.DataFrame(rows, columns=["date", "tmin_F", "tmax_F", "ETo_in", "ETc_in", "trigger", "drip_hrs"])
print(out.to_string(index=False))
print(f"\nTrigger days: {int(out.trigger.sum())}/{len(out)}; total drip runtime {out.drip_hrs.sum():.1f} h")
