"""
Propagates real, cited measurement/model uncertainty through the chill,
GDD, and ETo models using real 2024 CIMIS data (station 262, Linden) --
reports the chill-met date, GDD accumulation, and a sample ETo value as
DISTRIBUTIONS (median + 90% interval) instead of single point predictions.

See models/uncertainty.py for exactly what's being propagated and why
(sensor systematic bias vs. Hargreaves' own structural error), and why
bias is drawn once per trial rather than resampled every hour.

Run:
    ./venv/bin/python analysis/07_uncertainty_propagation.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from models.chill import chill_requirement_met_date, SWEET_CHERRY_CHILL_HOURS_REQUIRED
from models.gdd import cumulative_gdd
from models.eto import hargreaves_eto_in
from models.uncertainty import (
    MonteCarloResult,
    draw_systematic_temp_bias,
    draw_hargreaves_structural_error_in,
    perturb_hourly_series,
    perturb_daily_minmax,
)

N_TRIALS = 2000
CHILL_START = pd.Timestamp("2023-11-01")
GDD_REFERENCE_DATE = pd.Timestamp("2024-03-15")  # fixed calendar point, not a bloom threshold guess
ETO_SAMPLE_DATE = pd.Timestamp("2024-04-15")
LODI_LATITUDE = 38.13

OUTPUT_PLOT = REPO_ROOT / "visualizations" / "04_uncertainty_propagation.png"


def load_real_2024_data():
    hourly = pd.read_csv(REPO_ROOT / "data" / "climate" / "cimis_lodi_hourly.csv", parse_dates=["timestamp"]).set_index("timestamp")
    daily = pd.read_csv(REPO_ROOT / "data" / "climate" / "cimis_lodi_daily.csv", parse_dates=["date"]).set_index("date")
    return hourly["hly_air_tmp"], daily["day_air_tmp_min"], daily["day_air_tmp_max"]


def run_monte_carlo(hourly_temp, daily_tmin, daily_tmax):
    rng = np.random.default_rng(2024)  # fixed seed: reproducible, not cherry-picked
    biases = draw_systematic_temp_bias(rng, N_TRIALS)
    structural_eto_errors = draw_hargreaves_structural_error_in(rng, N_TRIALS)

    chill_met_days_offset = []  # days relative to the deterministic (zero-bias) result
    gdd_at_reference = []
    eto_samples = []

    deterministic_chill_met = chill_requirement_met_date(hourly_temp, start=CHILL_START)

    for bias, struct_err in zip(biases, structural_eto_errors):
        perturbed_hourly = perturb_hourly_series(hourly_temp, bias)
        met = chill_requirement_met_date(perturbed_hourly, start=CHILL_START)
        if met is not None and deterministic_chill_met is not None:
            chill_met_days_offset.append((met - deterministic_chill_met).total_seconds() / 86400)

            p_tmin, p_tmax = perturb_daily_minmax(daily_tmin, daily_tmax, bias)
            gdd_series = cumulative_gdd(p_tmin, p_tmax, start=met.normalize())
            if GDD_REFERENCE_DATE in gdd_series.index:
                gdd_at_reference.append(gdd_series.loc[GDD_REFERENCE_DATE])

        if ETO_SAMPLE_DATE in daily_tmin.index:
            tmin_p = daily_tmin.loc[ETO_SAMPLE_DATE] + bias
            tmax_p = daily_tmax.loc[ETO_SAMPLE_DATE] + bias
            eto = hargreaves_eto_in(tmin_p, tmax_p, ETO_SAMPLE_DATE.dayofyear, LODI_LATITUDE) + struct_err
            eto_samples.append(max(eto, 0.0))  # ETo can't be physically negative

    return (
        deterministic_chill_met,
        MonteCarloResult(np.array(chill_met_days_offset)),
        MonteCarloResult(np.array(gdd_at_reference)),
        MonteCarloResult(np.array(eto_samples)),
    )


def main():
    hourly_temp, daily_tmin, daily_tmax = load_real_2024_data()
    det_chill_met, chill_offset, gdd_result, eto_result = run_monte_carlo(hourly_temp, daily_tmin, daily_tmax)

    print(f"=== Uncertainty propagation, real 2024 CIMIS data ({N_TRIALS} trials) ===\n")

    print(f"Deterministic (zero-bias) chill-met date: {det_chill_met}")
    s = chill_offset.summary()
    print(
        f"Chill-met date uncertainty: median {s['median']:+.1f} days, "
        f"90% CI [{s['p5']:+.1f}, {s['p95']:+.1f}] days relative to that date"
    )
    print(
        "  NOTE: check visualizations/04_uncertainty_propagation.png before quoting this as a\n"
        "  single +/- range -- the distribution is multimodal (clustered around a few discrete\n"
        "  offsets, not smoothly spread), because a handful of specific real days sit right at\n"
        "  the 45F chill threshold: small bias shifts flip whether THOSE days count, jumping the\n"
        "  chill-met date between a few candidate calendar dates rather than shifting it\n"
        "  continuously. A median/percentile summary is still valid, just less informative than\n"
        "  it would be for a unimodal distribution -- the histogram is the real answer here.\n"
    )

    s = gdd_result.summary()
    print(f"Cumulative GDD by {GDD_REFERENCE_DATE.date()} (from each trial's own chill-met date):")
    print(f"  median {s['median']:.0f} GDD-F, 90% CI [{s['p5']:.0f}, {s['p95']:.0f}]\n")

    s = eto_result.summary()
    print(f"ETo on {ETO_SAMPLE_DATE.date()} (sensor bias + Hargreaves structural error combined):")
    print(f"  median {s['median']:.3f} in/day, 90% CI [{s['p5']:.3f}, {s['p95']:.3f}]")
    print(
        f"  (for reference, the deterministic single-point estimate ignoring all uncertainty "
        f"would just be the median trial's value -- the spread here IS the finding)"
    )

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    axes[0].hist(chill_offset.values, bins=30, color="tab:blue")
    axes[0].set_title("Chill-met date shift (days)")
    axes[0].set_xlabel("Days relative to zero-bias estimate")

    axes[1].hist(gdd_result.values, bins=30, color="tab:orange")
    axes[1].set_title(f"Cumulative GDD by {GDD_REFERENCE_DATE.date()}")
    axes[1].set_xlabel("GDD-F")

    axes[2].hist(eto_result.values, bins=30, color="tab:green")
    axes[2].set_title(f"ETo on {ETO_SAMPLE_DATE.date()} (in/day)")
    axes[2].set_xlabel("in/day")

    fig.suptitle("Monte Carlo uncertainty propagation -- real 2024 CIMIS data, station 262")
    fig.tight_layout()
    OUTPUT_PLOT.parent.mkdir(exist_ok=True)
    fig.savefig(OUTPUT_PLOT, dpi=130)
    print(f"\nSaved {OUTPUT_PLOT}")


if __name__ == "__main__":
    main()
