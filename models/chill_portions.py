"""
The Dynamic Model (Fishman et al. 1987a,b; Erez, Fishman, Linsley-Noakes
& Allan 1990) -- the more accurate alternative to the simple chill-hours
threshold count in models/chill.py, and the model UC ANR's own research
validates specifically for 'Bing' sweet cherry in California (see
sources below). Ported faithfully from chillR's Dynamic_Model function
(Luedeling et al., the standard peer-reviewed reference implementation
in R), not reconstructed from memory -- the exact index arithmetic here
matters and was checked line-by-line against chillR's source
(github.com/cran/chillR, R/temp_models.R).

WHY THIS IS MORE ACCURATE than counting threshold hours: the Dynamic
Model represents chill accumulation as a two-step biochemical process.
Cold hours build up an intermediate ("precursor") product, but that
precursor is REVERSIBLE -- a warm spell before it converts can tear it
back down, unlike the simple hours model where warm hours simply don't
count (they don't actively undo progress). Only once the precursor
crosses a threshold does it convert into one irreversible "chill
portion" -- and once formed, a portion can never be erased by later
warmth. This reversible-then-irreversible structure is a real,
documented improvement in predictive accuracy over simple threshold
counting (see the Bing-cherry validation study cited below).

UNITS: this module takes temperature in Fahrenheit (this project's
convention throughout) and converts to Celsius internally, since the
model's published constants (E0, E1, A0, A1, slope, Tf) are calibrated
for a Celsius-based Kelvin conversion (TK = T_celsius + 273). Getting
this unit conversion wrong would silently produce meaningless output --
flagged here on purpose.

WHAT'S DELIBERATELY NOT INCLUDED: a "chill portions required" threshold
for this orchard/cultivar. Chill Portions and Chill Hours are different
units (not linearly convertible), and unlike the 700-800h chill-hours
figure in models/chill.py, a solid citation for sweet cherry's specific
chill-PORTION requirement wasn't found during this project's research --
inventing a number here would be worse than leaving it uncalibrated.
See analysis/09_chill_portions_real_data.py for what this module IS
used for: computing and comparing the real accumulation curve, without
claiming a specific completion threshold.

Sources:
- Fishman, Erez, Linsley-Noakes, Allan (1987a,b, 1990) -- original model.
- Luedeling et al., chillR package (CRAN) -- reference implementation
  these constants and this algorithm are ported from.
- "Evaluation of Chill Models in 'Bing' Sweet Cherry Rest-breaking
  Trials in California... Validation of the Dynamic Model" -- confirms
  this specific model for this specific California cherry variety.
- "One chill portion equals ~28 hours at 6C (43F)"; optimal constant
  temperature ~5.1C, >40h needed for one portion there; ~12.1C is
  approximately where accumulation stops -- cited benchmarks used in
  this module's own tests (models/tests/test_chill_portions.py).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# Published constants (Fishman et al.; as used in chillR's Dynamic_Model).
E0 = 4153.5
E1 = 12888.8
A0 = 139500.0
A1 = 2.567e18
SLOPE = 1.6
TF_KELVIN = 277.0  # ~4C


def _fahrenheit_to_celsius(temp_f: np.ndarray) -> np.ndarray:
    return (temp_f - 32) * 5 / 9


def dynamic_model_cumulative_portions(hourly_temp_f: pd.Series) -> pd.Series:
    """
    hourly_temp_f: hourly air temperature (F), evenly spaced, no gaps
        (this model is a genuine hour-to-hour recurrence, not a simple
        count -- unlike models/chill.py it cannot tolerate missing hours
        without introducing real error, so gaps should be filled/
        interpolated by the caller first if the real series has them).
    Returns cumulative chill portions, same index as the input.
    """
    n = len(hourly_temp_f)
    if n < 2:
        raise ValueError("need at least 2 hourly readings to run the Dynamic Model recurrence")

    temp_c = _fahrenheit_to_celsius(hourly_temp_f.to_numpy(dtype=float))
    tk = temp_c + 273.0

    aa = A0 / A1
    ee = E1 - E0
    sr = np.exp(SLOPE * TF_KELVIN * (tk - TF_KELVIN) / tk)
    xi = sr / (1 + sr)
    xs = aa * np.exp(ee / tk)
    eak1 = np.exp(-A1 * np.exp(-E1 / tk))

    x = np.zeros(n)
    for i in range(1, n):
        s = x[i - 1]
        if x[i - 1] >= 1:
            s = s * (1 - xi[i - 2])  # i>=2 whenever this branch is reachable, since x[0]=0 < 1 always
        x[i] = xs[i - 1] - (xs[i - 1] - s) * eak1[i - 1]

    delta = np.zeros(n)
    completed = np.where(x >= 1)[0]
    delta[completed] = x[completed] * xi[completed - 1]

    return pd.Series(np.cumsum(delta), index=hourly_temp_f.index)
