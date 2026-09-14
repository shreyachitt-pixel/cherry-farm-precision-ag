"""
Turns real gravimetric calibration samples (raw ADC + wet/dry mass) into a
raw-ADC -> volumetric water content (VWC) conversion, and picks the
best-supported functional form rather than assuming linearity.

See data/calibration/README.md for the physical procedure this consumes.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class SampleMoisture:
    gwc: float           # gravimetric water content, g water / g dry soil
    bulk_density: float  # g dry soil / cm3 total volume
    vwc: float           # volumetric water content, cm3 water / cm3 total volume


def compute_sample_moisture(
    gross_wet_mass_g: float,
    gross_dry_mass_g: float,
    container_tare_g: float,
    container_volume_cm3: float,
) -> SampleMoisture:
    wet_soil_g = gross_wet_mass_g - container_tare_g
    dry_soil_g = gross_dry_mass_g - container_tare_g
    if dry_soil_g <= 0:
        raise ValueError("dry soil mass must be positive -- check tare/mass inputs")
    water_g = wet_soil_g - dry_soil_g
    gwc = water_g / dry_soil_g
    bulk_density = dry_soil_g / container_volume_cm3
    # water density ~1 g/cm3, so cm3 of water ~= grams of water
    vwc = water_g / container_volume_cm3
    return SampleMoisture(gwc=gwc, bulk_density=bulk_density, vwc=vwc)


@dataclass
class FitResult:
    form: str  # "linear", "inverse_linear", "quadratic"
    coefficients: list[float]  # highest-degree first, numpy.polyfit convention
    r_squared: float
    adjusted_r_squared: float
    n_samples: int

    def predict(self, adc: float) -> float:
        x = 1.0 / adc if self.form == "inverse_linear" else adc
        return float(np.polyval(self.coefficients, x))


def _r_squared(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    if ss_tot == 0:
        return 1.0 if ss_res == 0 else 0.0
    return 1.0 - ss_res / ss_tot


def _adjusted_r_squared(r2: float, n: int, p: int) -> float:
    """p = number of predictors (not counting the intercept)."""
    if n - p - 1 <= 0:
        return float("-inf")  # not enough data to penalize meaningfully
    return 1 - (1 - r2) * (n - 1) / (n - p - 1)


def _fit_polynomial(x: np.ndarray, y: np.ndarray, degree: int, form_name: str) -> FitResult:
    coeffs = np.polyfit(x, y, degree)
    y_pred = np.polyval(coeffs, x)
    r2 = _r_squared(y, y_pred)
    return FitResult(
        form=form_name,
        coefficients=list(coeffs),
        r_squared=r2,
        adjusted_r_squared=_adjusted_r_squared(r2, len(x), degree),
        n_samples=len(x),
    )


def fit_linear(adc: np.ndarray, vwc: np.ndarray) -> FitResult:
    return _fit_polynomial(np.asarray(adc, dtype=float), np.asarray(vwc, dtype=float), 1, "linear")


def fit_inverse_linear(adc: np.ndarray, vwc: np.ndarray) -> FitResult:
    inv_adc = 1.0 / np.asarray(adc, dtype=float)
    return _fit_polynomial(inv_adc, np.asarray(vwc, dtype=float), 1, "inverse_linear")


def fit_quadratic(adc: np.ndarray, vwc: np.ndarray) -> FitResult:
    return _fit_polynomial(np.asarray(adc, dtype=float), np.asarray(vwc, dtype=float), 2, "quadratic")


def select_best_fit(adc: np.ndarray, vwc: np.ndarray) -> tuple[FitResult, list[FitResult]]:
    """
    Fits all supported forms and picks the one with the highest ADJUSTED R^2
    (penalizes the quadratic's extra parameter rather than always preferring
    it just because it has more freedom to fit noise). Quadratic is skipped
    below 5 samples -- fitting 3 parameters to 4 or fewer points isn't a
    meaningful fit, it's interpolation.
    """
    n = len(adc)
    candidates = [fit_linear(adc, vwc), fit_inverse_linear(adc, vwc)]
    if n >= 5:
        candidates.append(fit_quadratic(adc, vwc))
    best = max(candidates, key=lambda f: f.adjusted_r_squared)
    return best, candidates
