"""
Critical spring frost temperatures for sweet cherry by bud development
stage, and a two-tier (WATCH/WARNING) risk classifier -- the mechanism
behind the frost-alert monitor.

Buds get dramatically more cold-sensitive as they develop: a dormant
swollen bud shrugs off temperatures that would kill 90% of open flowers.
This is why "frost risk" isn't a single number -- it depends on what
stage the buds are actually in when the cold hits.

Source: Michigan State University Extension, "Critical Spring
Temperatures" (canr.msu.edu/cherries/weather/critical-spring-temperatures),
a standard reference used across extension services. Values are the
temperature (F) causing 10% bud kill and 90% bud kill at each stage.
"""

from __future__ import annotations

from dataclasses import dataclass

# Ordered earliest -> latest stage. (stage_name, temp_10pct_kill_F, temp_90pct_kill_F)
CRITICAL_TEMPS_F = [
    ("dormant_swollen_bud", 17, 5),
    ("side_green", 22, 9),
    ("green_tip", 25, 14),
    ("tight_cluster", 26, 17),
    ("open_cluster", 27, 21),
    ("first_white", 27, 24),
    ("first_bloom", 28, 25),
    ("full_bloom", 28, 25),
    ("post_bloom_shuck", 28, 25),
]

STAGE_ORDER = [s[0] for s in CRITICAL_TEMPS_F]
_THRESHOLDS = {name: (t10, t90) for name, t10, t90 in CRITICAL_TEMPS_F}

DEFAULT_STAGE_BEFORE_CHILL_MET = "dormant_swollen_bud"
DEFAULT_STAGE_AFTER_CHILL_MET = "full_bloom"  # conservative: most sensitive stage


@dataclass
class FrostAssessment:
    level: str  # "none", "watch", "warning"
    stage: str
    forecast_low_f: float
    temp_10pct_kill_f: int
    temp_90pct_kill_f: int


def assess_frost_risk(forecast_low_f: float, stage: str) -> FrostAssessment:
    if stage not in _THRESHOLDS:
        raise ValueError(f"Unknown bud stage '{stage}'. Valid: {STAGE_ORDER}")
    t10, t90 = _THRESHOLDS[stage]
    if forecast_low_f <= t90:
        level = "warning"  # at/below 90%-kill threshold
    elif forecast_low_f <= t10:
        level = "watch"  # at/below 10%-kill threshold but above 90%-kill
    else:
        level = "none"
    return FrostAssessment(
        level=level,
        stage=stage,
        forecast_low_f=forecast_low_f,
        temp_10pct_kill_f=t10,
        temp_90pct_kill_f=t90,
    )
