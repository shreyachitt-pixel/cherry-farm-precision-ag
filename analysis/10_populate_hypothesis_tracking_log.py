"""
Populates data/hypothesis_tracking/log.csv with real, precisely-defined
predictor/outcome values for each year -- but computes NO test
statistic and NO p-value. That's the entire point: see
analysis/PRE_REGISTRATION.md for why testing is deferred until enough
years accumulate. This script only builds the evidence record so that
when that day comes, the values are already computed from a
pre-specified, code-defined method -- not reconstructed (and possibly
adjusted) after the fact.

Operational definitions (must match PRE_REGISTRATION.md exactly --
if this script's method ever changes, that's a dated amendment there,
not a silent edit here):

  H1 predictor: hours classified WATCH-or-worse (i.e. any real frost
    risk, not just the stricter WARNING tier) by models/frost_risk.py at
    the conservative "full_bloom" stage, in the window from that year's
    chill-met date through +60 days.
  H2 predictor: days with real max temp >=95F in the PRIOR summer
    (Jun 1 - Aug 31 of year N-1) -- the flower-bud-initiation window
    for year N's crop.
  H3 predictor: total real precipitation in the 25 days before the
    recorded/estimated harvest date (NA for a year with no harvest).
  H4 predictor: cumulative chill portions (Dynamic Model) by March 1.
  Outcome: total_yield_lbs_delivered from data/yield/yield_history.csv.

Run:
    ./venv/bin/python analysis/10_populate_hypothesis_tracking_log.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from models.chill import chill_requirement_met_date
from models.chill_portions import dynamic_model_cumulative_portions
from models.frost_risk import assess_frost_risk
from models.data_coverage import has_adequate_coverage

LOG_PATH = REPO_ROOT / "data" / "hypothesis_tracking" / "log.csv"

BLOOM_RISK_WINDOW_DAYS = 60
CHILL_REFERENCE_MONTH_DAY = (3, 1)  # March 1
PREHARVEST_RAIN_WINDOW_DAYS = 25


def load_climate():
    hourly = pd.read_csv(REPO_ROOT / "data" / "climate" / "cimis_lodi_hourly.csv", parse_dates=["timestamp"]).set_index("timestamp")["hly_air_tmp"]
    daily = pd.read_csv(REPO_ROOT / "data" / "climate" / "cimis_lodi_daily.csv", parse_dates=["date"]).set_index("date")
    return hourly, daily


def h1_frost_risk_hours(hourly, chill_start, year) -> float | None:
    """
    Counts hours at WATCH-or-worse (i.e. any non-'none' level), not just
    WARNING -- a more complete operationalization of "frost exposure"
    decided during pre-registration DESIGN, before any commit locks it in.

    IMPORTANT DOCUMENTED TENSION, found while building this predictor and
    left exactly as found rather than "fixed": the actual 2026 frost
    reading (29.2F) doesn't reach WATCH level either -- it's classified
    'none' at full_bloom, because it's actually ABOVE that stage's
    10%-kill threshold (28F) in the MSU table models/frost_risk.py uses.
    So H1, as operationalized here from the published table, would show
    ZERO risk hours for the very year we currently believe had a
    damaging frost. That is NOT patched by loosening the threshold
    further -- doing so now, after already knowing which year needs to
    be flagged, would be circular (tuning a definition to guarantee it
    "detects" a known outcome is a textbook pre-registration violation).
    Registering the honest, literature-grounded definition and letting
    it possibly fail to detect 2026 is itself informative: if H1 keeps
    finding nothing as more years accumulate, that's real evidence
    against the simple threshold-exceedance explanation, and grounds for
    a SEPARATELY pre-registered hypothesis later (e.g. a duration-based
    or multi-night-compounding frost model) -- not a retroactive edit
    to this one.
    """
    chill_search_end = chill_start + pd.Timedelta(days=200)  # generous window to find chill-met within
    if not has_adequate_coverage(hourly.index, chill_start, chill_search_end, expected_per_day=24):
        return None
    window = hourly.loc[chill_start:chill_search_end]
    met = chill_requirement_met_date(window, start=chill_start)
    if met is None:
        return None
    risk_end = met + pd.Timedelta(days=BLOOM_RISK_WINDOW_DAYS)
    if not has_adequate_coverage(hourly.index, met, risk_end, expected_per_day=24):
        return None
    risk_window = hourly.loc[met:risk_end]
    at_risk = risk_window.apply(lambda t: assess_frost_risk(t, "full_bloom").level != "none")
    return float(at_risk.sum())


def h2_prior_summer_heat_days(daily, year) -> float | None:
    start = pd.Timestamp(year=year - 1, month=6, day=1)
    end = pd.Timestamp(year=year - 1, month=8, day=31)
    if not has_adequate_coverage(daily.index, start, end, expected_per_day=1):
        return None
    window = daily.loc[start:end, "day_air_tmp_max"]
    return float((window >= 95).sum())


def h3_preharvest_rain_in(daily, harvest_date) -> float | None:
    if harvest_date is None:
        return None
    start = harvest_date - pd.Timedelta(days=PREHARVEST_RAIN_WINDOW_DAYS)
    if not has_adequate_coverage(daily.index, start, harvest_date, expected_per_day=1):
        return None
    window = daily.loc[start:harvest_date, "day_precip"]
    return float(window.sum())


def h4_chill_portions_by_march1(hourly, chill_start, year) -> float | None:
    ref_date = pd.Timestamp(year=year, month=CHILL_REFERENCE_MONTH_DAY[0], day=CHILL_REFERENCE_MONTH_DAY[1])
    if not has_adequate_coverage(hourly.index, chill_start, ref_date, expected_per_day=24):
        return None
    window = hourly.loc[chill_start:ref_date]
    portions = dynamic_model_cumulative_portions(window)
    return float(portions.iloc[-1])


def main():
    hourly, daily = load_climate()
    yield_df = pd.read_csv(REPO_ROOT / "data" / "yield" / "yield_history.csv")

    rows = []
    for _, y in yield_df.iterrows():
        year = int(y["year"])
        chill_start = pd.Timestamp(year=year - 1, month=11, day=1)
        harvest_date = pd.to_datetime(y["harvest_date_approx"]) if pd.notna(y.get("harvest_date_approx")) else None

        rows.append({
            "year": year,
            "yield_lbs": y["total_yield_lbs_delivered"] if pd.notna(y["total_yield_lbs_delivered"]) else None,
            "h1_bloom_frost_risk_hours": h1_frost_risk_hours(hourly, chill_start, year),
            "h2_prior_summer_heat_days_95f": h2_prior_summer_heat_days(daily, year),
            "h3_preharvest_rain_in": h3_preharvest_rain_in(daily, harvest_date),
            "h4_chill_portions_by_mar1": h4_chill_portions_by_march1(hourly, chill_start, year),
        })

    log = pd.DataFrame(rows)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    log.to_csv(LOG_PATH, index=False)
    print(f"Wrote {len(log)} year(s) to {LOG_PATH}\n")
    print(log.to_string(index=False))
    print(
        "\nNo test statistic computed -- see analysis/PRE_REGISTRATION.md for why. "
        "This is an evidence log, not an analysis."
    )


if __name__ == "__main__":
    main()
