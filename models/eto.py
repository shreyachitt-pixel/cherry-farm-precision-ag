"""
Reference evapotranspiration (ETo) via the Hargreaves-Samani method.

CIMIS publishes ETo computed with the more data-hungry FAO-56 Penman-Monteith
method (needs solar radiation, wind, dewpoint). Hargreaves only needs daily
min/max air temperature and the site's latitude, which makes it usable both
on our synthetic data and as a sanity check against the real CIMIS ETo once
that's wired in (the two should track closely, even if not identical).

Reference: Hargreaves, G.H. & Samani, Z.A. (1985); FAO Irrigation and
Drainage Paper 56, Chapter 4 (for the Ra formulas).
"""

from __future__ import annotations

import math

SOLAR_CONSTANT_MJ = 0.0820  # Gsc, MJ m-2 min-1, FAO-56 eq. 28


def _inverse_relative_distance(day_of_year: int) -> float:
    """dr in FAO-56 eq. 23."""
    return 1 + 0.033 * math.cos(2 * math.pi / 365 * day_of_year)


def _solar_declination(day_of_year: int) -> float:
    """delta in FAO-56 eq. 24, radians."""
    return 0.409 * math.sin(2 * math.pi / 365 * day_of_year - 1.39)


def _sunset_hour_angle(latitude_rad: float, declination_rad: float) -> float:
    """omega_s in FAO-56 eq. 25, radians."""
    x = -math.tan(latitude_rad) * math.tan(declination_rad)
    x = min(1.0, max(-1.0, x))  # guard polar edge cases
    return math.acos(x)


def extraterrestrial_radiation_mj(day_of_year: int, latitude_deg: float) -> float:
    """
    Ra: extraterrestrial radiation in MJ m-2 day-1 (FAO-56 eq. 21).
    day_of_year: 1-365/366. latitude_deg: positive for northern hemisphere
    (Lodi, CA is ~38.1 N).
    """
    lat_rad = math.radians(latitude_deg)
    dr = _inverse_relative_distance(day_of_year)
    delta = _solar_declination(day_of_year)
    omega_s = _sunset_hour_angle(lat_rad, delta)
    return (
        (24 * 60 / math.pi)
        * SOLAR_CONSTANT_MJ
        * dr
        * (
            omega_s * math.sin(lat_rad) * math.sin(delta)
            + math.cos(lat_rad) * math.cos(delta) * math.sin(omega_s)
        )
    )


def hargreaves_eto_mm(tmin_c: float, tmax_c: float, tmean_c: float, ra_mj: float) -> float:
    """
    ETo in mm/day, Hargreaves-Samani equation:
        ETo = 0.0023 * (Tmean + 17.8) * sqrt(Tmax - Tmin) * Ra
    Ra is expressed here in mm/day-equivalent via the 0.408 conversion
    factor (1 MJ m-2 day-1 = 0.408 mm day-1 of evaporation-equivalent).
    """
    tmax_minus_tmin = max(tmax_c - tmin_c, 0.0)
    ra_mm = 0.408 * ra_mj
    return 0.0023 * (tmean_c + 17.8) * math.sqrt(tmax_minus_tmin) * ra_mm


def hargreaves_eto_in(
    tmin_f: float, tmax_f: float, day_of_year: int, latitude_deg: float = 38.13
) -> float:
    """ETo in inches/day from daily min/max air temp in Fahrenheit."""
    tmin_c = (tmin_f - 32) * 5 / 9
    tmax_c = (tmax_f - 32) * 5 / 9
    tmean_c = (tmin_c + tmax_c) / 2
    ra_mj = extraterrestrial_radiation_mj(day_of_year, latitude_deg)
    eto_mm = hargreaves_eto_mm(tmin_c, tmax_c, tmean_c, ra_mj)
    return eto_mm / 25.4
