"""
Crop water use (ETc) and drip irrigation scheduling.

ETc = ETo x Kc x Kr

  ETo: reference evapotranspiration (models.eto, or real CIMIS data once
       wired in) — how much a well-watered reference grass surface would
       use.
  Kc:  crop coefficient — converts reference (grass) water use to actual
       cherry water use, and changes through the season. UC/FAO literature
       puts sweet cherry Kc in the ~0.30 (dormant/early) to ~0.80 (peak
       canopy, pre-harvest) range; STAGE_KC below is a first-pass table
       that should get refined against the California Cherry Board's
       research report once accessible, or against real soil-moisture
       sensor response.
  Kr:  canopy/ground-cover reduction factor for young or widely spaced
       trees not yet shading the whole orchard floor — defaults to 1.0
       (full-canopy assumption) and should be lowered for young trees.

The runtime conversion (inches of water needed -> drip system minutes) is
plain volume/area arithmetic: 1 inch of water over 1 sq ft is exactly
0.6233 gallons.
"""

from __future__ import annotations

GALLONS_PER_SQFT_INCH = 0.6233  # 1 ft^2 x 1 in = 1/12 ft^3 = 7.48052/12 gal

# Approximate Kc by days since predicted bloom start. Refine once real
# fruit-development-stage observations exist.
STAGE_KC = [
    (0, 0.30),  # bloom / early leaf-out
    (21, 0.45),  # post-bloom fruit set
    (42, 0.65),  # pit hardening
    (63, 0.80),  # pre-harvest, full canopy
    (84, 0.75),  # post-harvest maintenance
]


def kc_for_days_since_bloom(days_since_bloom: int) -> float:
    """Piecewise-linear interpolation over STAGE_KC."""
    if days_since_bloom <= STAGE_KC[0][0]:
        return STAGE_KC[0][1]
    if days_since_bloom >= STAGE_KC[-1][0]:
        return STAGE_KC[-1][1]
    for (d0, kc0), (d1, kc1) in zip(STAGE_KC, STAGE_KC[1:]):
        if d0 <= days_since_bloom <= d1:
            frac = (days_since_bloom - d0) / (d1 - d0)
            return kc0 + frac * (kc1 - kc0)
    raise AssertionError("unreachable")


def etc_inches(eto_in: float, kc: float, kr: float = 1.0) -> float:
    return eto_in * kc * kr


def net_irrigation_in(etc_in: float, effective_rain_in: float) -> float:
    """Water still needed after accounting for rain that actually
    infiltrated (effective rainfall is usually a fraction of total
    rainfall — light rain mostly evaporates or runs off)."""
    return max(etc_in - effective_rain_in, 0.0)


def drip_runtime_hours(
    depth_in: float,
    wetted_area_sqft: float,
    emitters_per_tree: int,
    flow_gph_per_emitter: float,
) -> float:
    """
    depth_in: net irrigation depth needed (inches), e.g. from
        net_irrigation_in().
    wetted_area_sqft: area actually covered by the drip emitters per tree
        (not full canopy footprint — the wetted circle/strip under the
        emitters).
    emitters_per_tree, flow_gph_per_emitter: drip system hardware.
    Returns hours to run the system to deliver that depth.
    """
    gallons_needed = depth_in * wetted_area_sqft * GALLONS_PER_SQFT_INCH
    system_flow_gph = emitters_per_tree * flow_gph_per_emitter
    if system_flow_gph <= 0:
        raise ValueError("system_flow_gph must be positive")
    return gallons_needed / system_flow_gph
