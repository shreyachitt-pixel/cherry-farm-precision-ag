# Open items

Last updated: 2026-09-14. This is the real, checkable status list for
the project -- update it here as items close, rather than tracking
status anywhere that isn't committed to the repo.

## Before using this project in a college application

- [ ] **Make the GitHub repo public** (or grant specific reviewer
  access) -- it's currently **private**, so the link in the Common App
  Activities List / Additional Information draft (see below) is not
  actually viewable by admissions readers yet. This needs a decision
  and an action before the application is submitted.
- [ ] **Write the actual personal essays** (MIT's 4 short essays;
  Stanford's Intellectual Vitality essay). This project has real
  material mapped to each prompt (see conversation), but the essays
  themselves need to be written by Shreya, in her own voice -- not
  drafted here.
- [x] Common App Activities List line + Additional Information
  research-elaboration abstract -- drafted, character/word counts
  verified (147 chars / 143 words).

## Real data still needed

- [ ] **2025 exact yield figure.** Reported verbally as "a good year"
  but no document/number found yet. `data/yield/yield_history.csv`
  has this row as pending. Likely exists in a 2025 packing-house
  settlement statement (structured like the 2024 one already in the
  photographed batch) that hasn't been produced/photographed yet.
- [ ] **2026 crop failure: exact cause and timing.** Currently
  attributed to "weather -- frost and/or heat" per the grower's own
  account, with a real Feb 20-21, 2026 frost (29.2F) as the leading
  data-supported candidate -- but note the real, documented tension:
  that reading doesn't reach even WATCH level in the MSU critical-
  temperature table at full bloom (see
  `analysis/PRE_REGISTRATION.md`'s H1 section). More specific
  observation (which week bloom/fruit set actually happened, whether
  anything else was noticed) would help.
- [ ] **Soil moisture sensor calibration.** Protocol and fitting code
  are built and tested (`data/calibration/README.md`,
  `models/soil_moisture_calibration.py`), but need real gravimetric
  samples from the actual farm soil -- dig samples at 5-6 moisture
  levels, weigh wet/dry, record the sensor's raw reading, fill in
  `data/calibration/soil_moisture_calibration_TEMPLATE.csv`.
- [ ] **station_3 doesn't exist yet.** No third sensor station has
  been deployed.
- [x] **Field-check the station_2 sensor-2 dry reading.** Confirmed
  2026-09-27: a clogged sprinkler line near the `soil_moisture_2` probe
  was starving that spot of water (real dry pocket, not a sensor
  fault) -- cleared and fixed. Full record in
  `data/field_hypotheses_log.md`. Still worth checking the next real
  station_2 export to confirm the reading recovers now that the clog
  is cleared.

## Ongoing maintenance (recurring, not one-time)

- [ ] **Keep real sensor + CIMIS data flowing without gaps**,
  especially through the mid-June-late-July flower-bud-initiation
  window and the next Jan-April bloom/frost window -- the hypothesis-
  tracking log (`data/hypothesis_tracking/log.csv`) already shows real
  gaps (2021-2023, 2025) where predictors can't be computed because
  the climate data simply wasn't pulled for those windows.
- [ ] **Run the frost-alert monitor regularly through the Jan-April
  2027 bloom window** (`analysis/04_frost_alert_monitor.py`). Nothing
  runs this automatically yet -- it needs to be run manually each time,
  or scheduled (ask to set up a recurring check as the season
  approaches).
- [ ] **Re-run `analysis/10_populate_hypothesis_tracking_log.py`**
  whenever new real yield or climate data lands, to keep the evidence
  log current. Per `analysis/PRE_REGISTRATION.md`, no hypothesis gets
  formally tested until n=8 real bearing years exist (currently 2) --
  updating the log is not the same act as testing it.
- [ ] **Re-run `analysis/05_export_dashboard_data.py`** and refresh
  `site/` after any of the above changes, so the dashboard stays
  accurate rather than quietly going stale.
