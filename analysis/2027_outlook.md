# 2027 outlook and recommendations

**Bottom line up front: we cannot forecast 2027's actual yield.** Weather
6+ months out isn't reliably predictable, and yield depends on specific
weather events (a single cold night, a single hot week) that no seasonal
outlook can pin down this far in advance. What follows is what can
honestly be said from (1) a real, current seasonal climate outlook, (2)
real 2026 CIMIS data already in this repo, and (3) published cherry
phenology research -- plus concrete actions that follow from each.

## 1. The seasonal outlook: a very strong El Nino is coming

As of August 2026, NOAA's Climate Prediction Center puts a **>90% chance
of a very strong El Nino** for fall/winter 2026-27, with the wet season
peaking **January-March 2027** -- which is exactly the farm's likely
bloom window (chill was satisfied by late January in both 2024 and 2026,
per `analysis/02_real_calibration_2024_2026.py`).

What a wetter, stormier bloom window plausibly means, based on how these
mechanisms actually work:

- **Lower radiational frost risk.** The Feb 20-21, 2026 frost (29.2F,
  the leading suspect for that year's crop failure) is the classic
  clear-sky, calm-night radiational frost pattern. Rain/cloud cover
  generally keeps nights warmer by trapping outgoing heat -- so a wetter
  El Nino bloom window is *probably* somewhat protective against a repeat
  of exactly that failure mode. This is not a guarantee: cold, clear
  breaks between storms still happen in El Nino winters, and advective
  (wind-driven) frost isn't helped by cloud cover the same way.
- **Higher disease and pollination risk instead.** More rain during
  bloom raises fungal disease pressure (already in this project's scope
  -- humidity/rain is a known driver), and honeybees don't forage in
  rain or high humidity (WSU Tree Fruit, cited in `README.md`), so a
  wetter bloom window can suppress pollination even without any frost at
  all. The risk profile shifts, it doesn't simply improve.
- **Chill is not a concern.** Both real years on record met the ~750
  chill-hour requirement well before bloom, so an unusually cold winter
  wouldn't help and isn't needed.

**Action:** plan for wet-weather contingencies at bloom time, not just
frost. Have a fungicide/disease-prevention plan ready to trigger off
rain forecasts, and consider whether hive stocking density needs to be
higher to compensate for fewer good bee-flying hours if bloom coincides
with a stormy stretch.

## 2. Summer 2026 heat may already be shaping the 2027 crop

Sweet cherry flower buds for **next year's** bloom are initiated during
the *current* summer -- in Mediterranean climates (Lodi's climate type),
this window runs roughly **mid-June through late July**. Floral bud
development during this window is documented to be sensitive to heat and
drought stress, which can reduce the number and viability of buds set
for the following spring.

Real CIMIS data for this exact farm shows heat spikes landing squarely
in that window in 2026:

| Date | Max temp |
|---|---|
| Jun 11-13, 2026 | 97.8-97.9F |
| Jul 14-15, 2026 | 99.4-100.3F |
| Jul 21, 2026 | 98.7F |
| Jul 31, 2026 | 96.2F |

**This is an honest gap in the project, not a finding:** the farm's own
soil-moisture sensors weren't deployed and reporting yet during this
window (station_1/station_2 data only starts Aug 25, 2026 -- see
`data/README.md`), so there's no real record of whether irrigation kept
up during these heat spikes. We can't say whether 2027's return bloom is
at risk from this -- only that it's a real, unverified possibility.

**Action, and the clearest lesson from this whole exercise:** get all
sensor stations running continuously *before* the next critical window,
not after. Concretely:
- Deploy/verify station_3 and confirm all three stations report through
  the winter and into next summer's bud-initiation window (Jun-Jul 2027)
  without gaps.
- Through fall 2026, maintain adequate irrigation and fertility
  regardless of what already happened this summer -- carbohydrate
  reserves built now still support next spring's bud quality.

## 3. Concrete frost-protection options for spring 2027 bloom

Given a real frost event is the leading suspect for 2026's failure, and
even a wetter El Nino winter doesn't eliminate frost risk, it's worth
having actual protection in place before the Feb-March 2027 bloom
window, not just a monitoring dashboard:

| Method | Protection | Constraints |
|---|---|---|
| Overhead sprinklers | Down to ~24F (latent heat of freezing water protects buds) | Needs wind < 10 mph; high water use |
| Wind machines | Raises temp ~1.1-2.8C by mixing warmer air down | Ineffective on very calm, deep-inversion nights; capital cost |
| Row covers / frost cloth | Modest protection for young trees | Labor-intensive to deploy/remove each night |

For a ~9-acre operation, overhead sprinklers or targeted frost cloth on
the most exposed rows are the more proportionate options versus a
wind-machine capital investment -- worth pricing out before next
February rather than during a frost warning.

**Action:** decide on and stage frost-protection equipment by January
2027, and treat the chill/frost dashboard (`models/chill.py` +
real-time CIMIS pulls) as the trigger to actually deploy it, not just to
observe after the fact.

## Sources

- [NOAA CPC ENSO strength probabilities](https://cpc.ncep.noaa.gov/products/analysis_monitoring/enso/roni/strengths.php)
- Floral induction timing/heat sensitivity: sweet cherry floral bud research (ScienceDirect, PLOS One -- see conversation research; mid-June-late July initiation window in Mediterranean climates, heat/drought sensitivity of the developing buds)
- Frost protection methods: Rutgers NJAES E363, Chelan Ranch wind machine guide, PSU Extension frost/critical temperatures guide
- WSU Tree Fruit: honeybee foraging temperature/weather limits
