import pytest

from models.eto import extraterrestrial_radiation_mj, hargreaves_eto_in


def test_ra_matches_fao56_worked_example():
    # FAO-56 (Allen et al. 1998), Example 8: latitude -20deg, day of year
    # 246 (3 Sept) -> Ra = 32.2 MJ m-2 day-1. Cross-checking our
    # implementation against the textbook's own worked example, not just
    # against itself.
    ra = extraterrestrial_radiation_mj(day_of_year=246, latitude_deg=-20)
    assert ra == pytest.approx(32.2, rel=0.03)


def test_ra_higher_in_local_summer_than_winter_northern_hemisphere():
    lodi_lat = 38.13
    summer_ra = extraterrestrial_radiation_mj(day_of_year=172, latitude_deg=lodi_lat)  # ~Jun 21
    winter_ra = extraterrestrial_radiation_mj(day_of_year=355, latitude_deg=lodi_lat)  # ~Dec 21
    assert summer_ra > winter_ra


def test_hargreaves_eto_positive_and_plausible_range():
    # Central Valley summer day: hot and dry
    summer_eto = hargreaves_eto_in(tmin_f=65, tmax_f=100, day_of_year=200, latitude_deg=38.13)
    # Central Valley winter day: cool
    winter_eto = hargreaves_eto_in(tmin_f=38, tmax_f=55, day_of_year=15, latitude_deg=38.13)

    assert 0 < winter_eto < summer_eto
    assert summer_eto < 0.6  # inches/day; a very hot Central Valley day is roughly this ballpark
