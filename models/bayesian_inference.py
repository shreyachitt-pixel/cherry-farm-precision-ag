"""
Generic grid-based Bayesian updating: prior x likelihood -> posterior, over
a 1-D parameter grid. Deliberately not MCMC -- for a single scalar
parameter, evaluating a grid directly is exact (up to grid resolution),
easy to verify, and easy to plot, so there's no reason to reach for
sampling machinery. See analysis/08_chill_threshold_inference.py for the
actual application (inferring the chill-hours threshold).

Why Bayesian inference at all, instead of fitting/regression: with only
one or two real years of soft, qualitative evidence, there isn't enough
data to fit a parameter the usual (frequentist, point-estimate) way
without wild overfitting -- the same reasoning that ruled out a
regression on 4 yield points elsewhere in this project. Bayesian
inference is the honest tool for "I have real prior knowledge (the
literature) and a little bit of weak evidence" -- weak evidence
correctly leaves the posterior close to the prior, rather than pretending
two data points can pin down a parameter precisely.
"""

from __future__ import annotations

import numpy as np


def normal_prior_density(theta_grid: np.ndarray, mean: float, std: float) -> np.ndarray:
    return (1.0 / (std * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((theta_grid - mean) / std) ** 2)


def normalize_density(theta_grid: np.ndarray, density: np.ndarray) -> np.ndarray:
    """Rescales density so it integrates to 1 over the grid (trapezoidal)."""
    area = np.trapezoid(density, theta_grid)
    if area <= 0:
        raise ValueError("density integrates to zero or less over this grid -- widen the grid or check inputs")
    return density / area


def bayesian_update(theta_grid: np.ndarray, prior_density: np.ndarray, likelihood: np.ndarray) -> np.ndarray:
    """posterior(theta) proportional to prior(theta) * likelihood(theta), renormalized."""
    unnormalized = prior_density * likelihood
    return normalize_density(theta_grid, unnormalized)


def posterior_mean(theta_grid: np.ndarray, density: np.ndarray) -> float:
    return float(np.trapezoid(theta_grid * density, theta_grid))


def posterior_std(theta_grid: np.ndarray, density: np.ndarray) -> float:
    mean = posterior_mean(theta_grid, density)
    variance = np.trapezoid(((theta_grid - mean) ** 2) * density, theta_grid)
    return float(np.sqrt(variance))


def credible_interval(theta_grid: np.ndarray, density: np.ndarray, level: float = 0.90) -> tuple[float, float]:
    """Equal-tailed credible interval: the (1-level)/2 and 1-(1-level)/2
    quantiles of the discretized posterior CDF."""
    cdf = np.cumsum(density) * np.gradient(theta_grid)
    cdf = cdf / cdf[-1]  # guard against small trapezoid/cumsum mismatch
    tail = (1 - level) / 2
    lower = float(np.interp(tail, cdf, theta_grid))
    upper = float(np.interp(1 - tail, cdf, theta_grid))
    return lower, upper
