# Yield history — real data

Fill in `yield_history_TEMPLATE.csv` (rename to `yield_history.csv` once
real values are in — the TEMPLATE name is a reminder not to treat the
placeholder as data) with the actual 4 years, then this becomes the
fourth real-data tier alongside `data/raw/` and `data/climate/`.

Columns:
- `year` — harvest year
- `total_yield` / `yield_unit` — whatever unit is actually tracked (lbs,
  boxes, tons — doesn't matter, just be consistent)
- `bloom_date_approx` — even a rough date (e.g. "mid-March") is useful:
  it's the real-world check for `models/gdd.py`'s bloom prediction, which
  currently has no calibrated threshold.
- `harvest_date_approx` — anchors the rain-cracking risk window (10-25
  days before this date) and the heat-stress window before it.
- `weather_notes` — anything remembered: a late frost, a big rain event
  near harvest, an unusually hot stretch, anything that stood out that
  year. Free text is fine — this is what turns a plain number into a
  usable case study.

## Why year-total yield only gets a case-study treatment, not a regression

Four (year, yield) pairs is not enough data to fit a real multivariable
model — with 4 points, "explaining" yield with 2-3 weather variables is
guaranteed overfitting, not a finding. `analysis/03_yield_drivers.py`
(next step) instead computes a handful of literature-grounded risk
indices per year from real historical CIMIS data — frost nights during
bloom, heat-stress days near harvest, rain inches in the pre-harvest
window, whether winter chill was fully met — and ranks/compares years
against those, plus simple one-variable-at-a-time correlations clearly
labeled as exploratory. That's the honest use of 4 data points: pattern
comparison, not prediction.

Reference thresholds used by that analysis (see full citations in the
project README):
- Rain-cracking risk: ~1.1 in of rain within 10-25 days before harvest is
  the cited damage threshold; >25% cracked fruit makes harvest
  uneconomical.
- Heat stress: daytime temps ≥33-37C (91-99F) during ripening measurably
  reduce yield.
- Bloom frost: any night at/below freezing during the bloom window is a
  yield risk for early-flowering cultivars.
- Bloom favorability: daytime temps ≥16C (61F) during bloom favor good
  pollination and fruit set.
