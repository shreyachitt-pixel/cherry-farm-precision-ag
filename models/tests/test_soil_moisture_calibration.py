import numpy as np
import pytest

from models.soil_moisture_calibration import (
    compute_sample_moisture,
    fit_linear,
    fit_inverse_linear,
    fit_quadratic,
    select_best_fit,
)


def test_compute_sample_moisture_known_values():
    # Container: 100 cm3, tare 20g. Wet soil 150g total -> 130g soil.
    # Dry soil 110g total -> 90g soil. Water = 130-90 = 40g.
    result = compute_sample_moisture(
        gross_wet_mass_g=150, gross_dry_mass_g=110, container_tare_g=20, container_volume_cm3=100
    )
    assert result.gwc == pytest.approx(40 / 90)  # water / dry soil
    assert result.bulk_density == pytest.approx(90 / 100)  # dry soil / volume
    assert result.vwc == pytest.approx(40 / 100)  # water / volume


def test_compute_sample_moisture_zero_dry_mass_raises():
    with pytest.raises(ValueError):
        compute_sample_moisture(
            gross_wet_mass_g=50, gross_dry_mass_g=20, container_tare_g=20, container_volume_cm3=100
        )


def test_fit_linear_recovers_known_line_exactly():
    # VWC = 0.0005 * adc - 1.4, sampled at known ADC points, no noise.
    adc = np.array([3000, 3100, 3200, 3300])
    vwc = 0.0005 * adc - 1.4
    result = fit_linear(adc, vwc)
    assert result.r_squared == pytest.approx(1.0, abs=1e-9)
    assert result.coefficients[0] == pytest.approx(0.0005, rel=1e-6)
    assert result.coefficients[1] == pytest.approx(-1.4, rel=1e-6)


def test_fit_inverse_linear_recovers_known_relationship():
    adc = np.array([2900, 3000, 3100, 3200])
    vwc = 500.0 / adc - 0.1  # exact linear-in-(1/adc) relationship
    result = fit_inverse_linear(adc, vwc)
    assert result.r_squared == pytest.approx(1.0, abs=1e-9)


def test_fit_quadratic_fits_a_parabola_better_than_linear():
    adc = np.array([2900, 3000, 3100, 3200, 3300, 3400])
    vwc = 1e-6 * (adc - 3100) ** 2 + 0.001 * adc  # genuinely curved relationship
    linear = fit_linear(adc, vwc)
    quad = fit_quadratic(adc, vwc)
    assert quad.r_squared > linear.r_squared


def test_select_best_fit_prefers_simpler_model_when_quadratic_gives_no_real_benefit():
    # Perfectly linear data: quadratic can only match, not beat, linear's R^2,
    # and adjusted R^2 must then penalize its extra parameter.
    adc = np.array([2900, 3000, 3100, 3200, 3300])
    vwc = 0.0004 * adc - 1.1
    best, candidates = select_best_fit(adc, vwc)
    assert best.form == "linear"
    assert len(candidates) == 3  # linear, inverse_linear, quadratic (n>=5)


def test_select_best_fit_skips_quadratic_below_five_samples():
    adc = np.array([3000, 3100, 3200, 3300])
    vwc = np.array([0.1, 0.15, 0.2, 0.22])
    _, candidates = select_best_fit(adc, vwc)
    assert {c.form for c in candidates} == {"linear", "inverse_linear"}


def test_fit_result_predict_uses_correct_input_transform():
    adc = np.array([2900, 3000, 3100, 3200])
    vwc = 500.0 / adc - 0.1
    result = fit_inverse_linear(adc, vwc)
    predicted = result.predict(3050)
    expected = 500.0 / 3050 - 0.1
    assert predicted == pytest.approx(expected, abs=1e-6)
