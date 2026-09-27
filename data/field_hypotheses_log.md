# Field hypotheses log

Separate from `analysis/PRE_REGISTRATION.md` (which pre-registers
statistical yield-driver hypotheses tested across years -- see that
file's own scope). This log is for smaller, operational hypotheses
about specific sensors/locations that are resolved by a physical check
in the field, not a statistical test. Same habit, different kind of
claim: write down the guess and how it'll be checked *before* checking,
so the record shows what was predicted rather than what was found.

Each entry: date raised, source, the hypothesis, what would confirm or
rule it out, and the outcome once checked (or "PENDING").

---

## 2026-09-27: Sensor-2 dry reading -- fault vs. real dry pocket

**Raised by:** Kamesh Chitti (farm advisor), reviewing the 12 real
station_2 readings in `data/raw/sensordata.csv`.

**Observation:** In 2 of the 12 readings, `soil_moisture_2` reads 2000
and 1947 while `soil_moisture_1` reads ~3000+ in the same readings.
Every other reading has the two sensors within ~150 counts of each
other (see the validation in this project's chat history / commit log
around this date).

**Two competing hypotheses, both still open:**
- **H-field-1 (sensor fault):** the two low readings are a bad
  connection or a dislodged probe, not a real moisture difference.
  Weakly favored by the data alone: later readings return straight to
  ~3150-3260 with no gradual recovery, which is more consistent with a
  fault clearing than soil drying out and re-wetting.
- **H-field-2 (real dry pocket):** the sensor sits in a spot with a
  sprinkler/drip coverage gap, and the reading reflects genuinely drier
  soil there. If a tree is near that sensor, this would help explain
  any visible stress on that tree.

**How this gets resolved (not a statistical test):**
1. Walk out to the physical location of the `soil_moisture_2` probe on
   station_2.
2. Check the soil by hand (dig a small hole, feel/see moisture) and
   compare to the area around `soil_moisture_1`.
3. Check the sprinkler/drip pattern reaching that spot -- is there a
   visible gap or dry ring under/near the emitter?
4. Check the sensor's physical connection and placement (fully seated
   in soil, not exposed to air, wiring intact).
5. If a tree is near that sensor, note its condition (leaf color,
   wilting, any visible stress) independent of the sensor reading, so
   the tree observation isn't biased by already knowing the sensor
   value.

**Outcome:** RESOLVED -- see 2026-09-27 entry below.

---

## 2026-09-27: Field-check result -- H-field-2 confirmed

**Checked by:** Shreyas.

**Finding:** The sprinkler line near the `soil_moisture_2` probe on
station_2 was clogged, which was starving that spot of water. The line
was cleared and fixed on the spot.

**Which hypothesis this supports:** H-field-2 (real dry pocket from a
sprinkler coverage gap) -- the 2000/1947 readings reflected genuinely
drier soil there, not a sensor fault. H-field-1 (sensor fault) is ruled
out for these two readings.

**Not yet confirmed, and not claimed here:** soil moisture by hand at
the probe, the exact tree's visible condition before the fix, and
whether `soil_moisture_2` readings return to the ~3150-3260 range on
the next real export after the clog was cleared. Worth checking the
next export against this once new station_2 data comes in -- if the
sensor stays low even with the clog cleared, that would reopen the
sensor-fault possibility for a different reason (fault plus clog were
both present).

**Caveat carried forward:** the two anomalous readings had `device_counter`
values of 1 and 622, not real timestamps, so the exact date/time this
clog started (and thus how long that spot went under-watered) can't be
pinned down from the data alone -- only from whenever the clog was
actually found and fixed.
