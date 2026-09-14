"""
Infers the orchard's real chill-hours requirement instead of assuming
literature's 750-hour midpoint, using real 2024/2026 CIMIS data and the
two years' actual outcomes as weak evidence -- Bayesian inference, not
regression, because two years of soft evidence is nowhere near enough to
fit a parameter the usual way (the same reasoning that ruled out
regressing yield on 4 points elsewhere in this project). This script
does NOT change models/chill.py's default -- it's a separate, clearly
labeled research exercise; see the bottom of this file for why.

THE EVIDENCE, precisely, and its real uncertainty:
- 2024: a good harvest resulted despite real hard freezes Jan 7-12 (down
  to 25.5F). This is more consistent with the trees NOT having reached a
  frost-sensitive bloom stage yet during that freeze window than with
  them having been in active bloom -- i.e., whatever the true chill
  threshold is, it more plausibly implies chill (and the bloom-sensitive
  stage that follows it) came LATER than Jan 12.
- 2026: a real frost event Feb 20-21 (29.2F) is the leading candidate for
  that year's total crop failure -- which requires the buds to have
  already reached a frost-sensitive stage BY Feb 20-21, i.e. chill (and
  the sensitive stage that follows) more plausibly came EARLIER than
  Feb 21.

These two years pull in OPPOSITE directions (2024 wants a later
chill-met date relative to its freeze window, 2026 wants an earlier one
relative to its frost date) -- which is exactly what makes this a real
(if weak) two-point constraint rather than one year just restating the
literature prior.

KNOWN COMPLICATION, stated plainly rather than glossed over: the MSU
critical-temperature table (models/frost_risk.py) puts full-bloom's
10%-kill threshold at 28F -- so 29.2F, the actual 2026 frost reading,
sits ABOVE that threshold and by that table alone wouldn't obviously
explain a TOTAL crop failure. Frost is still the leading hypothesis
(nothing else in the real data fits better -- see
analysis/02_real_calibration_2024_2026.py), but this script's evidence
for 2026 assumes frost really was the cause; if that assumption is wrong,
this half of the inference is built on sand. Flagged here on purpose.

Run:
    ./venv/bin/python analysis/08_chill_threshold_inference.py
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

from models.chill import chill_requirement_met_date
from models.bayesian_inference import (
    normal_prior_density,
    normalize_density,
    bayesian_update,
    posterior_mean,
    posterior_std,
    credible_interval,
)

# --- Prior: UC Davis Fruit & Nut Research Center cites ~700-800h as
# typical for sweet cherry, 350-1200h across varieties. Treating 700-800
# as roughly the prior's central 50% interval gives std ~= 50/0.6745 =
# 74; using 75 as a round number. This choice is a modeling assumption,
# stated plainly, not itself derived from data.
PRIOR_MEAN = 750.0
PRIOR_STD = 75.0
THETA_GRID = np.linspace(300, 1300, 10_001)

# --- Likelihood shaping assumptions (also modeling choices, not
# empirical facts): how many days after chill-met before buds reach a
# frost-sensitive stage (rough phenological lag), and how "soft" vs
# "hard" the date boundary is treated.
LAG_BUFFER_DAYS = 21
SOFTNESS_DAYS = 7.0

CHILL_START_2024 = pd.Timestamp("2023-11-01")
FREEZE_REFERENCE_2024 = pd.Timestamp("2024-01-12")  # last of the Jan 7-12 hard-freeze cluster

CHILL_START_2026 = pd.Timestamp("2025-11-01")
FROST_REFERENCE_2026 = pd.Timestamp("2026-02-21")


def sigmoid(x: np.ndarray) -> np.ndarray:
    # Clipped, not a precision loss in practice: sigmoid is already
    # indistinguishable from 0/1 well before +-500, but the "chill never
    # reached" sentinel (-9999 days) would otherwise overflow exp().
    return 1.0 / (1.0 + np.exp(-np.clip(x, -500, 500)))


def chill_met_dates_for_grid(hourly_temp: pd.Series, chill_start: pd.Timestamp, theta_grid: np.ndarray) -> list:
    return [chill_requirement_met_date(hourly_temp, start=chill_start, required_hours=int(theta)) for theta in theta_grid]


def likelihood_2024(dates: list, freeze_ref: pd.Timestamp) -> np.ndarray:
    # HIGH when chill-met + lag lands safely AFTER the freeze (buds not yet
    # sensitive during it); LOW when it would land before/during the freeze.
    margins = np.array([
        ((d + pd.Timedelta(days=LAG_BUFFER_DAYS)) - freeze_ref).days if d is not None else -9999
        for d in dates
    ])
    return sigmoid(margins / SOFTNESS_DAYS)


def likelihood_2026(dates: list, frost_ref: pd.Timestamp) -> np.ndarray:
    # HIGH when chill-met + lag lands safely BEFORE the frost (buds already
    # sensitive when it hit, consistent with frost causing the failure);
    # LOW when it would land after (trees likely still dormant, undermining
    # the frost hypothesis for that theta).
    margins = np.array([
        (frost_ref - (d + pd.Timedelta(days=LAG_BUFFER_DAYS))).days if d is not None else -9999
        for d in dates
    ])
    return sigmoid(margins / SOFTNESS_DAYS)


def main():
    hourly_2024 = pd.read_csv(REPO_ROOT / "data" / "climate" / "cimis_lodi_hourly.csv", parse_dates=["timestamp"]).set_index("timestamp")["hly_air_tmp"]
    hourly_2026 = hourly_2024  # same file covers both real windows already pulled

    print("Computing chill-met date across the parameter grid for both real years "
          f"({len(THETA_GRID)} grid points)...")
    dates_2024 = chill_met_dates_for_grid(hourly_2024.loc["2023-11-01":"2024-06-01"], CHILL_START_2024, THETA_GRID)
    dates_2026 = chill_met_dates_for_grid(hourly_2026.loc["2025-11-01":"2026-09-13"], CHILL_START_2026, THETA_GRID)

    lik_2024 = likelihood_2024(dates_2024, FREEZE_REFERENCE_2024)
    lik_2026 = likelihood_2026(dates_2026, FROST_REFERENCE_2026)
    combined_likelihood = lik_2024 * lik_2026

    prior = normalize_density(THETA_GRID, normal_prior_density(THETA_GRID, PRIOR_MEAN, PRIOR_STD))
    posterior = bayesian_update(THETA_GRID, prior, combined_likelihood)

    prior_ci = credible_interval(THETA_GRID, prior, 0.90)
    post_ci = credible_interval(THETA_GRID, posterior, 0.90)
    post_mean = posterior_mean(THETA_GRID, posterior)
    post_std = posterior_std(THETA_GRID, posterior)

    print(f"\nPrior (literature):  mean={PRIOR_MEAN:.0f}h, 90% interval [{prior_ci[0]:.0f}, {prior_ci[1]:.0f}]h")
    print(f"Posterior (real data): mean={post_mean:.0f}h, std={post_std:.0f}h, "
          f"90% credible interval [{post_ci[0]:.0f}, {post_ci[1]:.0f}]h")

    shift = post_mean - PRIOR_MEAN
    width_ratio = (post_ci[1] - post_ci[0]) / (prior_ci[1] - prior_ci[0])
    print(f"\nPosterior mean shifted {shift:+.0f}h from the prior; "
          f"credible interval is {width_ratio:.0%} the width of the prior's.")
    if width_ratio > 0.85:
        print(
            "  That's barely narrower than the prior -- correct behavior given how weak this\n"
            "  evidence actually is (two years of soft, assumption-laden qualitative signal).\n"
            "  This should NOT be read as 'we've pinned down the threshold' -- it's evidence\n"
            "  that two years isn't enough to move far past the literature default, which is\n"
            "  itself a legitimate, honest finding, not a null result."
        )

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(THETA_GRID, prior, label=f"Prior (UC Davis lit.): N({PRIOR_MEAN:.0f}, {PRIOR_STD:.0f})", linestyle="--")
    ax.plot(THETA_GRID, posterior, label="Posterior (given 2024 + 2026 real outcomes)")
    ax.axvline(PRIOR_MEAN, color="gray", linewidth=1, linestyle=":")
    ax.set_xlabel("Chill-hours requirement (theta)")
    ax.set_ylabel("Probability density")
    ax.set_title("Chill-threshold inference: literature prior vs. real-data posterior")
    ax.legend()
    fig.tight_layout()
    out_path = REPO_ROOT / "visualizations" / "05_chill_threshold_posterior.png"
    fig.savefig(out_path, dpi=130)
    print(f"\nSaved {out_path}")

    print(
        "\nmodels/chill.py's SWEET_CHERRY_CHILL_HOURS_REQUIRED is intentionally left at the\n"
        "literature value (750h) despite this result -- the evidence here rests on several\n"
        "stacked assumptions (the LAG_BUFFER_DAYS phenology lag, that frost was really the\n"
        "2026 cause, that 'good/bad outcome' maps cleanly onto 'sensitive stage or not') that\n"
        "aren't themselves validated. This script's job is to show what real data DOES and\n"
        "DOESN'T support, not to silently swap in a shakier number."
    )


if __name__ == "__main__":
    main()
