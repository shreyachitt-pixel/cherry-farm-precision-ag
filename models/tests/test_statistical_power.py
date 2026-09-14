import pytest

from models.statistical_power import required_n_for_correlation, achieved_power_for_n


@pytest.mark.parametrize("r,expected_n", [
    (0.10, 783),  # Cohen (1988): small effect
    (0.30, 85),   # Cohen (1988): medium effect
    (0.50, 28),   # Cohen (1988): large effect
])
def test_required_n_matches_cohens_published_table(r, expected_n):
    # alpha=.05 two-tailed, power=.80 -- the standard convention Cohen's
    # own tables use. Small tolerance for rounding-convention differences
    # across sources (783 vs 782, 28 vs 29, etc.).
    n = required_n_for_correlation(r, alpha=0.05, power=0.80, two_tailed=True)
    assert n == pytest.approx(expected_n, abs=2)


def test_required_n_decreases_as_effect_size_grows():
    small = required_n_for_correlation(0.1)
    medium = required_n_for_correlation(0.3)
    large = required_n_for_correlation(0.7)
    assert small > medium > large


def test_required_n_increases_with_higher_power_target():
    n_80 = required_n_for_correlation(0.5, power=0.80)
    n_95 = required_n_for_correlation(0.5, power=0.95)
    assert n_95 > n_80


def test_invalid_r_raises():
    with pytest.raises(ValueError):
        required_n_for_correlation(0.0)
    with pytest.raises(ValueError):
        required_n_for_correlation(1.0)


def test_achieved_power_is_near_80_percent_at_cohens_required_n():
    # Consistency check between the two functions: plugging Cohen's own
    # required-n for r=.5 back in should recover ~80% power.
    n = required_n_for_correlation(0.5, power=0.80)
    power = achieved_power_for_n(round(n), r=0.5)
    assert power == pytest.approx(0.80, abs=0.03)


def test_achieved_power_is_very_low_at_small_real_sample_sizes():
    # The actual finding this project's pre-registration rests on: with
    # only a handful of real bearing years, power to detect even a large
    # effect (r=.5) is far below any conventional threshold.
    power_at_5_years = achieved_power_for_n(5, r=0.5)
    assert power_at_5_years < 0.25


def test_achieved_power_increases_with_n():
    p5 = achieved_power_for_n(5, r=0.5)
    p15 = achieved_power_for_n(15, r=0.5)
    p30 = achieved_power_for_n(30, r=0.5)
    assert p5 < p15 < p30
