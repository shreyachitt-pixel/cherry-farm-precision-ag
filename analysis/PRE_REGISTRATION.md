# Pre-Registration: Environmental Driver Hypotheses for Cherry Yield

**Status:** REGISTERED. **Registration date:** 2026-09-13. **Locking commit:**
recorded in `data/hypothesis_tracking/README.md` immediately after this
file is first committed (the git commit hash + timestamp is the actual
proof this was written before later years' outcomes were known -- see
"Registration lock" at the bottom).

Any change to the hypotheses, predictors, tests, or thresholds below
**after** the locking commit must be added to the Amendments Log at the
bottom with a date and a stated reason. Nothing above the Amendments Log
gets silently edited.

## Why this document exists

`analysis/02_real_calibration_2024_2026.py` already did legitimate
**exploratory** analysis on the two real years available (2024, 2026):
it looked at the data, noticed patterns (a real frost event near the
2026 failure, a bloom-date discrepancy in 2024), and reported them
honestly, including their uncertainty. That's the right thing to do
with 2 data points, and it's *not* the same thing as a confirmatory
statistical test -- treating an exploratory finding as if it were a
tested result is exactly how researchers fool themselves and each other.
The named failure modes:

- **HARKing** (Hypothesizing After the Results are Known) -- noticing a
  pattern in the data, then presenting it as if it had been predicted
  in advance.
- **The garden of forking paths** -- trying several reasonable variable
  definitions/thresholds and reporting whichever one happens to look
  significant, without disclosing the others were tried.
- **Optional stopping** -- checking the result after each new year
  arrives and deciding *then* whether to call it "enough data," which
  inflates the false-positive rate far above the stated significance
  level.

This document exists to make all of those structurally impossible for
the hypotheses below: the variables, the tests, the significance
threshold, and the minimum sample size are fixed **now**, before most of
the data that will be used even exists.

## How much data this actually requires (real numbers, not a guess)

Using `models/statistical_power.py` (Cohen 1988's method, validated in
`models/tests/test_statistical_power.py` against Cohen's own published
table values):

| True effect size (r) | n needed for 80% power (alpha=.05, two-tailed) |
|---|---|
| 0.3 (medium) | 85 |
| 0.5 (large) | 29 |
| 0.7 (very large / near-deterministic) | 13 |

And the reverse question -- what power do we actually have at the
sample sizes we're likely to have soon:

| n (bearing years) | Power to detect r=0.5 | Power to detect r=0.7 |
|---|---|---|
| 5 | 12% | 23% |
| 8 | 23% | 49% |
| 10 | 31% | 63% |
| 15 | 48% | 85% |
| 20 | 62% | 95% |

**Decision:** no hypothesis below will be formally tested (a p-value
computed and compared to alpha) before **n = 8 bearing years** of data
exist for it, and even then the result will be reported as a clearly
labeled low-power, exploratory-strength look (power 23-49% is far
below the 80% convention) -- not treated as confirmatory. Real
confidence, even for a dramatic near-deterministic effect, realistically
needs 13-15+ years; for a moderate effect it needs closer to 30. This
project currently has real climate+yield data for **2 bearing years**
(2024, 2026) -- nowhere close. That gap, stated in real numbers, is the
entire justification for this document existing instead of a results
section.

## Multiple comparisons

Four hypotheses are pre-registered below. Using a per-test alpha of .05
across all four would inflate the real false-positive rate well above
5%. Bonferroni correction is used: **alpha = .05 / 4 = .0125** per test.
This makes the already-large required-n numbers above even larger in
practice -- an honest cost of testing four things instead of committing
to just one, disclosed here rather than quietly ignored.

## The hypotheses

Each predictor is computed by a specific, already-written, tested
function -- see `analysis/10_populate_hypothesis_tracking_log.py` for
the exact code. If that code's method ever needs to change, that's a
dated amendment below, not a silent edit to the script.

### H1: Frost exposure during the bloom-risk window reduces yield

- **Predictor:** hours classified WATCH-or-worse by `models/frost_risk.py`
  (MSU critical-temperature table) at the conservative "full_bloom"
  stage, counted over the 60 days following that year's chill-met date
  (from `models/chill.py`).
- **Outcome:** total yield (lbs delivered).
- **Test:** Spearman rank correlation (robust to the skewed, zero-heavy
  distribution already visible in the real data).
- **Direction:** two-tailed, despite having a strong directional prior
  (more frost exposure should mean lower yield), as the more
  conservative default -- a one-tailed test was considered and rejected
  specifically to avoid the appearance of tuning the test for an easier
  significance threshold.
- **A documented tension, found while building this predictor and left
  exactly as found:** the real Feb 20-21, 2026 frost reading (29.2°F)
  does not even reach WATCH level at the full_bloom stage in the MSU
  table -- it sits *above* that stage's 10%-bud-kill threshold (28°F).
  So H1, honestly computed from the published table, currently shows
  **zero** risk hours for the very year believed to have had a damaging
  frost (see the real log in `data/hypothesis_tracking/log.csv`). This
  was **not** patched by loosening the threshold, because doing so after
  already knowing which year "should" be flagged would be circular --
  a definition tuned to guarantee it detects a known outcome is not a
  test of anything. If H1 keeps finding nothing as more years
  accumulate, that is itself real evidence against the simple
  threshold-exceedance explanation for 2026, and would motivate a
  **separately pre-registered** hypothesis (e.g. a duration-based or
  multi-night-compounding frost model) later -- not a retroactive edit
  here.

### H2: Summer heat during flower-bud initiation reduces the *following* year's yield

- **Predictor:** count of real days with max temp >=95°F in the prior
  summer (Jun 1 - Aug 31 of year N-1) -- the literature-documented
  flower-bud-initiation window for year N's crop (see
  `analysis/2027_outlook.md`'s sources).
- **Outcome:** total yield in year N (note the deliberate one-year lag).
- **Test:** Spearman rank correlation.
- **A structural cost specific to this hypothesis, disclosed in
  advance:** because each data point spans two calendar years (summer
  of N-1, yield of N), this hypothesis needs *more* real calendar years
  of climate data than H1/H3/H4 to reach the same n -- effectively
  costing one extra "wasted" year at each end of the available record.

### H3: Pre-harvest rain increases cracking-driven yield loss

- **Predictor:** total real precipitation in the 25 days before the
  recorded/estimated harvest date (the literature's cited 10-25-day
  rain-cracking risk window -- see this project's `README.md` sources).
- **Outcome:** total yield.
- **Test:** Spearman rank correlation.
- **Known gap:** undefined (NA) for any year with no harvest event at
  all (e.g. 2026) -- a total crop failure before fruit exists isn't a
  cracking event, so that year is correctly excluded from this specific
  test, not coded as a zero.

### H4: Winter chill sufficiency is associated with yield

- **Predictor:** cumulative chill portions (`models/chill_portions.py`,
  the Dynamic Model) accumulated by March 1.
- **Outcome:** total yield.
- **Test:** Spearman rank correlation.
- **Stated prior expectation, for the record:** based on exploratory
  work so far, both real years comfortably exceeded typical chill
  requirements well before bloom (see
  `analysis/02_real_calibration_2024_2026.py` and
  `analysis/09_chill_portions_real_data.py`), so the working assumption
  going into this registration is that chill is **not** the limiting
  factor at this site. This hypothesis is registered anyway because a
  working assumption that can't be falsified isn't doing any work --
  if H4 someday finds a real association, that would be a genuine
  surprise worth taking seriously, not a foregone negative result.

## What this project will NOT do

- Will not compute a p-value for any hypothesis before its n=8 gate,
  regardless of how interesting the partial data looks.
- Will not add, drop, or redefine a hypothesis after seeing a given
  year's yield number without logging it as a dated amendment below.
- Will not try alternate predictor definitions or thresholds (e.g. a
  different heat-day cutoff, a different rain window) and report only
  the one that looks best -- the garden of forking paths this document
  exists to close off.
- Will not treat reaching n=8 as license to keep re-testing every year
  after that looking for the first year a result crosses significance
  (optional stopping) -- once the minimum-n gate is reached, the test
  is run and reported at that point, and subsequent additional years
  are new evidence for the *next* scheduled look, not grounds to retry
  the same test repeatedly until it passes.

## The living evidence log

`data/hypothesis_tracking/log.csv`, populated by
`analysis/10_populate_hypothesis_tracking_log.py`, holds the real,
precisely-defined predictor and outcome values for every year with
adequate real data coverage -- computed honestly as NaN/None when real
climate data doesn't actually cover the needed window (a real bug,
caught and fixed while building this: see `models/data_coverage.py`
and its tests). The log is meant to be re-run and appended to every
year regardless of how many years that makes -- building the evidence
record is not the same act as testing it, and keeping the log current
should not be read as a signal that a test is imminent.

## Registration lock

- **Date:** 2026-09-13
- **Locking commit:** see `data/hypothesis_tracking/README.md`, updated
  immediately after this file's first commit with that commit's hash.

## Amendments Log

*(Empty at registration. Any future change to the hypotheses, tests,
predictors, thresholds, or minimum-n gate above must be appended here
with a date and a stated reason, never edited into the sections above.)*
