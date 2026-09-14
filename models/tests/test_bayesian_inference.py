import numpy as np
import pytest

from models.bayesian_inference import (
    normal_prior_density,
    normalize_density,
    bayesian_update,
    posterior_mean,
    posterior_std,
    credible_interval,
)


def _grid():
    return np.linspace(0, 1500, 30_001)  # fine grid for numerical-integration accuracy


def test_normal_prior_density_matches_hand_formula_at_mean():
    grid = _grid()
    density = normal_prior_density(grid, mean=750, std=60)
    peak = density[np.argmin(np.abs(grid - 750))]
    expected_peak = 1.0 / (60 * np.sqrt(2 * np.pi))
    assert peak == pytest.approx(expected_peak, rel=1e-3)


def test_normalize_density_integrates_to_one():
    grid = _grid()
    density = normal_prior_density(grid, mean=750, std=60)
    normalized = normalize_density(grid, density)
    assert np.trapezoid(normalized, grid) == pytest.approx(1.0, rel=1e-3)


def test_flat_likelihood_leaves_posterior_equal_to_prior():
    grid = _grid()
    prior = normalize_density(grid, normal_prior_density(grid, mean=750, std=60))
    flat_likelihood = np.ones_like(grid)
    posterior = bayesian_update(grid, prior, flat_likelihood)
    np.testing.assert_allclose(posterior, prior, rtol=1e-6)


def test_posterior_matches_closed_form_gaussian_conjugate_update():
    # Classic conjugate case: Gaussian prior N(mu0, sigma0) updated against
    # a Gaussian-shaped likelihood centered at y with spread sigma_obs has a
    # KNOWN closed-form posterior mean/variance. If the grid machinery is
    # correct, its numerical posterior must match this exactly (up to grid
    # resolution) -- this is the real validation of bayesian_update/
    # posterior_mean/posterior_std, not just a sanity check.
    mu0, sigma0 = 750.0, 100.0
    y, sigma_obs = 900.0, 80.0

    grid = np.linspace(0, 2000, 200_001)
    prior = normalize_density(grid, normal_prior_density(grid, mu0, sigma0))
    likelihood = normal_prior_density(grid, mean=y, std=sigma_obs)  # Gaussian likelihood-as-function-of-theta
    posterior = bayesian_update(grid, prior, likelihood)

    expected_var = 1 / (1 / sigma0**2 + 1 / sigma_obs**2)
    expected_mean = expected_var * (mu0 / sigma0**2 + y / sigma_obs**2)
    expected_std = np.sqrt(expected_var)

    assert posterior_mean(grid, posterior) == pytest.approx(expected_mean, rel=1e-3)
    assert posterior_std(grid, posterior) == pytest.approx(expected_std, rel=1e-3)


def test_credible_interval_narrows_when_likelihood_is_informative():
    grid = _grid()
    prior = normalize_density(grid, normal_prior_density(grid, mean=750, std=200))
    prior_lo, prior_hi = credible_interval(grid, prior, level=0.90)

    sharp_likelihood = normal_prior_density(grid, mean=750, std=20)
    posterior = bayesian_update(grid, prior, sharp_likelihood)
    post_lo, post_hi = credible_interval(grid, posterior, level=0.90)

    assert (post_hi - post_lo) < (prior_hi - prior_lo)


def test_credible_interval_matches_prior_when_likelihood_flat():
    grid = _grid()
    prior = normalize_density(grid, normal_prior_density(grid, mean=750, std=60))
    posterior = bayesian_update(grid, prior, np.ones_like(grid))
    prior_ci = credible_interval(grid, prior, level=0.90)
    post_ci = credible_interval(grid, posterior, level=0.90)
    assert post_ci[0] == pytest.approx(prior_ci[0], abs=1.0)
    assert post_ci[1] == pytest.approx(prior_ci[1], abs=1.0)
