import pytest

from models.irrigation import (
    etc_inches,
    net_irrigation_in,
    drip_runtime_hours,
    kc_for_days_since_bloom,
)


def test_etc_inches():
    assert etc_inches(eto_in=0.25, kc=0.6, kr=1.0) == pytest.approx(0.15)


def test_net_irrigation_subtracts_rain_and_floors_at_zero():
    assert net_irrigation_in(etc_in=0.3, effective_rain_in=0.1) == pytest.approx(0.2)
    assert net_irrigation_in(etc_in=0.1, effective_rain_in=0.5) == 0.0


def test_drip_runtime_hours_known_conversion():
    # 1 inch over 10 sq ft = 6.233 gallons needed. 2 emitters x 1 gph = 2 gph
    # system flow rate -> 6.233 / 2 = 3.1165 hours.
    hours = drip_runtime_hours(
        depth_in=1.0, wetted_area_sqft=10.0, emitters_per_tree=2, flow_gph_per_emitter=1.0
    )
    assert hours == pytest.approx(3.1165, rel=1e-3)


def test_kc_interpolation_endpoints_and_midpoint():
    assert kc_for_days_since_bloom(0) == pytest.approx(0.30)
    assert kc_for_days_since_bloom(200) == pytest.approx(0.75)  # past last stage, clamps
    # halfway between day 0 (0.30) and day 21 (0.45)
    assert kc_for_days_since_bloom(10.5) == pytest.approx(0.375)
