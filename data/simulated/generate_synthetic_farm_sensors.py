"""
SYNTHETIC DATA -- NOT REAL MEASUREMENTS.

Extrapolates the 12 real farm readings in data/raw/sensordata.csv into a
30-minute synthetic station series. Air temperature and humidity follow the
REAL CIMIS Lodi hourly record (data/climate/cimis_lodi_hourly.csv); the other
channels are modeled from the real farm readings:

  - soil_temp: lagged, damped copy of air temp, offset/scaled to the real range
  - light_lux: solar-shaped daytime curve scaled to the real daytime lux range
  - soil_moisture_1/2: real baseline (faulty sensor-2 rows excluded) plus slow
    drift and noise sized from the real rows

Output: data/simulated/SYNTHETIC_farm_sensors.csv (every row is invented).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RNG = np.random.default_rng(42)
DAYS = 21

real = pd.read_csv(ROOT / "raw" / "sensordata.csv")
good = real[real.soil_moisture_2 > 2500]  # drop the 2 suspect sensor-2 reads

h = pd.read_csv(ROOT / "climate" / "cimis_lodi_hourly.csv", parse_dates=["timestamp"])
h = h.dropna(subset=["hly_air_tmp", "hly_rel_hum"]).set_index("timestamp")
h = h.iloc[-DAYS * 24:]
air_c = (h.hly_air_tmp - 32) * 5 / 9
idx = pd.date_range(h.index[0], h.index[-1], freq="30min")
air = air_c.reindex(idx).interpolate()
rh = h.hly_rel_hum.reindex(idx).interpolate()

# Air temp / humidity: CIMIS regional values, shifted by the farm-vs-CIMIS
# offset is unknowable without time-aligned readings, so none is applied.
soil_t = air.rolling(8, min_periods=1).mean()
lo, hi = real.soil_temp.min(), real.soil_temp.max()
soil_t = lo + (soil_t - soil_t.min()) / (soil_t.max() - soil_t.min()) * (hi - lo)

hour = idx.hour + idx.minute / 60
sun = np.clip(np.sin((hour - 6) / 12 * np.pi), 0, None)
day_lux = real.light_lux[real.light_lux > 100]
lux = sun * day_lux.quantile(0.75) * RNG.uniform(0.6, 1.4, len(idx))
lux = np.where(sun > 0, lux, 0.0)

n = len(idx)
drift = np.cumsum(RNG.normal(0, 1.5, n))
drift -= np.linspace(0, drift[-1], n) * 0.5
sm1 = good.soil_moisture_1.mean() + drift + RNG.normal(0, good.soil_moisture_1.std() * 0.3, n)
sm2 = good.soil_moisture_2.mean() + drift + RNG.normal(0, good.soil_moisture_2.std() * 0.3, n)

out = pd.DataFrame({
    "timestamp": idx, "station": "SYNTHETIC_farm", "soil_moisture_1": sm1.round(),
    "soil_moisture_2": sm2.round(), "air_temp": air.round(1).values,
    "humidity": rh.round(1).values, "soil_temp": soil_t.round(3).values,
    "light_lux": np.round(lux, 1),
})
out.to_csv(Path(__file__).parent / "SYNTHETIC_farm_sensors.csv", index=False)
print(f"wrote {len(out)} synthetic rows, {out.timestamp.min()} -> {out.timestamp.max()}")
