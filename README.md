# Cherry Farm Precision Agriculture

A real IoT sensor network and decision-support pipeline for a family cherry
farm in Lodi, CA — soil moisture, air temperature, humidity, soil
temperature, and light sensors feeding models for winter chill
accumulation, bloom-date prediction, bee-pollination timing, irrigation
scheduling, and pruning windows.

## Status

Real data is flowing. Two ESP32 stations have reported sensor data so
far (`station_3` doesn't exist yet; see `data/README.md` for exact
coverage and honest gaps). Real yield history (2021-2026, sourced from
crop-insurance and packing-house records — see `data/yield/`) is
calibrated against real CIMIS climate data for the Lodi area: a real
finding is that 2024's reported bloom date doesn't line up with the
chill/GDD model, and a real frost event on Feb 20-21, 2026 is the
leading candidate for that year's total crop failure — see
`analysis/02_real_calibration_2024_2026.py`. A frost-alert monitor
(`analysis/04_frost_alert_monitor.py`) pulls the real NWS 7-day forecast
and flags risk hours by bud stage. `analysis/2027_outlook.md` lays out
what's actually knowable about next season and what to do now.

## Why this exists

Soil moisture, air temperature, humidity, soil temperature, and light all
affect cherry development — fruit splitting from overwatering, fungal
disease risk from humidity, sugar development from light exposure. This
project turns those relationships into something measured and modeled
rather than guessed at, and ties them to concrete farm decisions:

- **When to introduce honeybee hives** for pollination (chill + GDD +
  temperature-gated bloom prediction)
- **How much and how often to irrigate** (ETo x Kc water-balance model,
  converted to actual drip system runtime)
- **When it's safe to prune** (phenology window + a weather-gated rule
  against pruning into wet conditions)
- **When to actually deploy frost protection** (real 7-day NWS forecast
  x bud-stage-specific critical temperatures, not just a generic "32F"
  threshold)

## Architecture

```
Farm sensors (ESP32, per station)   Real Lodi climate      Real 7-day
  soil moisture x2, air temp,       (CIMIS station 262)     NWS forecast
  humidity, soil temp, light              |                      |
         |                                v                      v
         v                    ingestion/cimis_client.py  ingestion/nws_forecast.py
   Google Sheet (posted via Wi-Fi)         |                      |
         |                                 |                      |
         v                                 v                      |
  ingestion/clean_raw_export.py   data/climate/                   |
         |                                 |                      |
         v                                 v                      |
      data/raw/            models/ (chill, gdd, eto, irrigation,  |
         |                          frost_risk) -- unit tested    |
         |                                 |                      |
         |                                 v                      v
         |                    analysis/02_real_calibration.py     |
         |                    (real yield vs. real climate)       |
         |                                                        v
         |                                       analysis/04_frost_alert_monitor.py
         v                                                        |
   analysis/01_eda.py                                    real-time risk alerts
         |
         v
   site/  (dashboard, GitHub Pages)
```

`data/simulated/` sits alongside `data/raw/` and `data/climate/` only to
let the models/dashboard be built and tested before enough real data
exists — see `data/README.md` for the ground rule on never treating it as
real.

## Repo layout

```
firmware/         ESP32 MicroPython — reads sensors, posts JSON
ingestion/         raw-export cleaning + CIMIS client + NWS forecast client
data/
  raw/              real sensor readings
  climate/          real CIMIS weather data + real NWS forecast pulls
  yield/            real yield history (crop insurance + packing house records)
  simulated/        SYNTHETIC data, clearly labeled, dev/test only
models/             chill, GDD, ETo, irrigation, frost_risk math — unit tested
  tests/
analysis/           EDA + real-data calibration + frost-alert monitor
visualizations/     generated plots
site/               dashboard (GitHub Pages)
```

## Setup

```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
./venv/bin/python -m pytest models/tests/ -v      # verify the math
./venv/bin/python analysis/01_eda.py               # real-data EDA
./venv/bin/python data/simulated/generate_synthetic_climate.py
./venv/bin/python analysis/00_synthetic_pipeline_demo.py
```

To pull real CIMIS climate data: copy `.env.example` to `.env`, fill in a
free CIMIS API key and the nearest station ID (see `.env.example`), then:
```bash
./venv/bin/python ingestion/cimis_client.py daily 2023-11-01 2024-06-01
./venv/bin/python ingestion/cimis_client.py hourly 2023-11-01 2024-06-01
./venv/bin/python analysis/02_real_calibration_2024_2026.py
```

To check real frost risk against the live 7-day forecast (no API key
needed — NWS's public API is free):
```bash
./venv/bin/python analysis/04_frost_alert_monitor.py
./venv/bin/python analysis/04_frost_alert_monitor.py --stage open_cluster
```

## Method notes / sources

- Chill hours: UC Davis Fruit & Nut Research and Information Center —
  sweet cherry needs roughly 700-800 chill hours below ~45F.
- ETo: Hargreaves-Samani method (FAO Irrigation and Drainage Paper 56),
  cross-checked in `models/tests/test_eto.py` against the paper's own
  worked example.
- Crop coefficient (Kc): sweet cherry ranges roughly 0.30-0.80 across the
  season per UC/FAO literature; the exact stage table in
  `models/irrigation.py` is a first pass that should be refined against
  real fruit-development observations.
- Pollination: honeybees generally won't forage below ~55-60F or in
  wind/rain; standard stocking is roughly 1-2 hives/acre placed at first
  bloom (WSU Tree Fruit, Oregon State Extension).
- Frost critical temperatures by bud stage (`models/frost_risk.py`):
  Michigan State University Extension's standard 10%/90%-bud-kill table
  — dormant buds survive down to single-digit F, open flowers are hurt
  by the mid-20s F.
- Forecast: NWS's free public API (api.weather.gov), ~7 days hourly, no
  key required.
