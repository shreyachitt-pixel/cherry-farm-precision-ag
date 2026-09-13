# Cherry Farm Precision Agriculture

A real IoT sensor network and decision-support pipeline for a family cherry
farm in Lodi, CA — soil moisture, air temperature, humidity, soil
temperature, and light sensors feeding models for winter chill
accumulation, bloom-date prediction, bee-pollination timing, irrigation
scheduling, and pruning windows.

## Status

Early. Two ESP32 stations have reported real data so far (`station_3`
doesn't exist yet); see `data/README.md` for exact coverage and honest
gaps. The chill/GDD/ETo/irrigation models are implemented and unit-tested
against literature reference values, and validated end-to-end against
synthetic (fabricated) climate data while a real CIMIS data feed is set
up. **Nothing in this repo currently represents a finished analysis of
the farm** — see `data/README.md` for what's real vs. synthetic.

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

## Architecture

```
Farm sensors (ESP32, per station)          Real Lodi climate data
  soil moisture x2, air temp,                (CIMIS station network)
  humidity, soil temp, light                          |
         |                                             |
         v                                             v
   Google Sheet (posted via Wi-Fi)          ingestion/cimis_client.py
         |                                             |
         v                                             |
  ingestion/clean_raw_export.py                        |
         |                                             |
         v                                             v
                  data/raw/  +  data/climate/
                            |
                            v
        models/  (chill.py, gdd.py, eto.py, irrigation.py)
                            |
                            v
              analysis/  (EDA, milestone predictions)
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
ingestion/         raw-export cleaning + CIMIS client
data/
  raw/              real sensor readings
  climate/          real CIMIS weather data (once configured)
  simulated/        SYNTHETIC data, clearly labeled, dev/test only
models/             chill, GDD, ETo, irrigation math — unit tested
  tests/
analysis/           EDA + pipeline scripts
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
free CIMIS API key and the nearest station ID (see `.env.example`), then
run `ingestion/cimis_client.py <start_date> <end_date>`.

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
