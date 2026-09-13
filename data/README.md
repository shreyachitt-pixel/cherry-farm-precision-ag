# Data provenance

This project keeps three data tiers in separate folders on purpose, so it's
always unambiguous what's a measurement and what's a model input or test
fixture. **Only `raw/` is real farm data.**

## `raw/` — real sensor readings

`sensordata.csv` is cleaned from the tab-delimited export the ESP32 stations
post to (via `ingestion/clean_raw_export.py`). As of the last export:

| Field | Coverage | First reading | Last reading |
|---|---|---|---|
| soil_moisture_1, soil_moisture_2 | 239/239 | 2026-08-25 | 2026-09-13 |
| air_temp, humidity (DHT22) | 232/239 | 2026-08-25 22:17 | 2026-09-13 |
| soil_temp (DS18B20) | 89/239 | intermittent throughout | 2026-09-13 |
| light_lux (BH1750) | 46/239 | 2026-09-06 16:40 | 2026-09-13 |

Notes on what actually happened, not a cleaned-up story:

- The first ~9 readings are soil-moisture-only — the DHT22 wasn't wired in
  yet at first deploy.
- `soil_temp` is sparse and intermittent rather than a clean before/after
  split — the DS18B20 connection looks unreliable rather than absent; worth
  checking the wiring/pull-up resistor on that probe.
- `light_lux` only starts 2026-09-06 — BH1750 was added partway through.
- **station_1** reported 2026-08-25 through 2026-08-29, then stopped.
  **station_2** starts 2026-09-05, six days later, with no overlap. That
  gap (dead power bank? station moved and re-flashed? Wi-Fi issue?) is
  worth writing down now, from memory, while it's fresh — it'll need an
  explanation in the analysis writeup, and "we don't actually know" is a
  legitimate answer if that's the truth.
- **station_3** has never reported. It doesn't exist as a device yet, or
  hasn't been deployed. The 3-station comparison in the original plan
  isn't real until it is.

New exports go through the same cleaning script and get appended here as
gathered. This file's coverage table should be regenerated (not hand-edited)
whenever new real data lands — see the snippet in `analysis/01_eda.py`.

## `climate/` — real public weather data (Lodi, CA)

Pulled from CIMIS (California Irrigation Management Information System),
the state's official ag weather network, via `ingestion/cimis_client.py`.
Nothing here is fabricated — it's historical/forecast records from an
actual station. Empty until a `CIMIS_API_KEY` is configured (see
`.env.example`).

## `simulated/` — synthetic data, clearly not real

Everything in this folder is generated, not measured. It exists only to
develop and test the pipeline (models, dashboard) before enough real data
accumulates, and it is never used as an input to any actual finding or
conclusion about the farm. Every file here carries `SYNTHETIC_` in its name
and a header comment saying so — if you ever see a plot or a number that
traces back to this folder, it describes the model working on invented
numbers, not the farm.
