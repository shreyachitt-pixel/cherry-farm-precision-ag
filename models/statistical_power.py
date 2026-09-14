"""
Sample-size / power calculations for a correlation test (Cohen 1988's
Fisher-z-transform method) -- the real math behind this project's
hypothesis-testing pre-registration (see
analysis/PRE_REGISTRATION.md): specifically, why none of the driver
hypotheses (frost/heat/rain vs. yield) are tested on the data that
exists yet, and how many years actually would be enough.

Method: transform r to Fisher's z = arctanh(r), whose sampling
distribution is (very nearly) normal with standard error 1/sqrt(n-3).
Solving for n at a target alpha/power gives Cohen's classic formula:

    n = ((z_(1-alpha/2) + z_(1-power)) / arctanh(r))^2 + 3

Validated in tests against Cohen's own commonly-cited published table
values (r=.10 -> ~783, r=.30 -> ~85, r=.50 -> ~28, at alpha=.05,
power=.80, two-tailed).
"""

from __future__ import annotations

import math


def _norm_ppf(p: float) -> float:
    """Inverse standard normal CDF (quantile function) via a rational
    approximation (Acklam's algorithm) -- avoids adding a scipy
    dependency for one function."""
    if not 0 < p < 1:
        raise ValueError("p must be in (0, 1)")
    # Coefficients for Acklam's approximation.
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    p_low = 0.02425
    if p < p_low:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
               ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p > 1 - p_low:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
                ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    q = p - 0.5
    r = q * q
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / \
           (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)


def _norm_cdf(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def required_n_for_correlation(r: float, alpha: float = 0.05, power: float = 0.80, two_tailed: bool = True) -> float:
    """Minimum sample size to detect a true correlation of magnitude r
    with the given alpha/power, via Cohen's Fisher-z method."""
    if not 0 < abs(r) < 1:
        raise ValueError("r must be strictly between -1 and 1 (and nonzero)")
    z_alpha = _norm_ppf(1 - alpha / (2 if two_tailed else 1))
    z_power = _norm_ppf(power)
    c = math.atanh(abs(r))
    return ((z_alpha + z_power) / c) ** 2 + 3


def achieved_power_for_n(n: int, r: float, alpha: float = 0.05, two_tailed: bool = True) -> float:
    """Inverse direction: given a sample size we actually expect to
    have, what power does that give us to detect a true correlation of
    magnitude r? (What the pre-registration actually needs to report:
    not just 'we need more data' but 'here is exactly how underpowered
    we are right now.')"""
    if n <= 3:
        return 0.0
    z_alpha = _norm_ppf(1 - alpha / (2 if two_tailed else 1))
    c = math.atanh(abs(r))
    z_power = c * math.sqrt(n - 3) - z_alpha
    return _norm_cdf(z_power)
