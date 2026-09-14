# Hypothesis tracking log

`log.csv` is the real evidence record for the hypotheses pre-registered
in `analysis/PRE_REGISTRATION.md`. Populated by running:

```bash
./venv/bin/python analysis/10_populate_hypothesis_tracking_log.py
```

Re-run this every time real yield or climate data is added (a new
year's yield number, a new CIMIS pull). It recomputes the full log from
scratch using the exact, fixed method described in
`analysis/PRE_REGISTRATION.md` -- it does not compute any test
statistic or p-value. Building the evidence record and testing it are
deliberately kept as two separate acts; see the pre-registration
document for why.

A value of NaN means real data doesn't yet adequately cover what that
predictor needs for that year (checked honestly by
`models/data_coverage.py`, not assumed) -- not zero, not "no effect."

## Registration lock

`analysis/PRE_REGISTRATION.md` was first committed at:

- **Commit:** `643682b` (also independently checkable via the commit
  timestamp on GitHub, not just this file's own claim)
- **Date:** 2026-09-13

This commit hash is the actual proof the hypotheses, predictors, and
tests were fixed before later years' outcomes were known -- not just
the stated registration date in the document itself.
