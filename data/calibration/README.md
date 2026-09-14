# Soil moisture sensor calibration protocol

The raw `soil_moisture_1`/`soil_moisture_2` readings in `data/raw/sensordata.csv`
are uncalibrated capacitive-sensor ADC counts (roughly 2990-3450 in the real
data so far) -- not a physical unit. This is the standard method (gravimetric
calibration) to convert them into real volumetric water content (VWC, cm3
water per cm3 of soil -- the physically meaningful quantity used in the
irrigation model).

Why this can't be skipped or guessed: capacitive sensor response depends on
the specific soil at this farm (texture, organic matter, bulk density) --
research shows sandy vs. clay soils produce meaningfully different
calibration curves for the identical sensor (see README.md sources). A
factory/generic calibration would carry real, uncharacterized error.

## What you need

- The actual sensor unit(s) currently deployed (or an identical spare) and
  something to read its raw ADC value (the ESP32 + a quick serial-print, or
  the `read_soil_moisture()` function in `firmware/main.py`)
- A kitchen/lab scale that reads to at least 0.1 g
- A small container of **known, fixed volume** (e.g. a 100 mL measuring cup)
  -- use the *same* container for every sample so `container_volume_cm3` is
  constant across rows
- An oven (or several days of air-drying) to dry soil samples
- Soil actually dug from the orchard, ideally near where the sensors sit

## Procedure (per sample)

1. Fill the container with a soil sample from the orchard at some moisture
   level. Collect samples across a *range* of moisture -- at minimum: air-dry,
   naturally moist, and saturated (add water and let it settle). 5-6 samples
   across that range gives enough points to tell whether the relationship is
   linear or not, rather than assuming.
2. Insert the sensor into that soil sample (in the container, or in the
   ground if the container is inserted into the sample site) and record the
   raw ADC reading.
3. Weigh the container + wet soil (`gross_wet_mass_g`).
4. Dry the sample: oven at ~220F (105C) until mass stops changing (a few
   hours), or air-dry for several days if no oven is available.
5. Weigh the container + dried soil (`gross_dry_mass_g`).
6. Weigh the empty container alone once (`container_tare_g`) -- this can be
   measured once and reused for every row that uses the same container.
7. Record everything in `soil_moisture_calibration_TEMPLATE.csv` (rename to
   `soil_moisture_calibration.csv` once real data is in, matching the
   convention used for `data/yield/`).

Repeat for `soil_moisture_2` as a separate set of rows if it's a physically
different sensor/location -- each sensor should get its own calibration,
since sensor-to-sensor manufacturing variation is real too.

## What the numbers become

`analysis/06_calibrate_soil_moisture.py` computes, per sample:

- **Gravimetric water content (GWC)** = (wet soil mass - dry soil mass) / dry soil mass
- **Bulk density** = dry soil mass / container volume
- **Volumetric water content (VWC)** = (wet soil mass - dry soil mass) / container volume

...then fits raw ADC -> VWC using linear, 1/ADC-linear, and quadratic forms,
reports R^2 for each (published results on this sensor type range from
~0.89 for a fitted polynomial to a 2-8% error rate against the gravimetric
method, so don't expect a perfect fit), and saves the best-fitting form's
coefficients to `data/calibration/fitted_calibration.json` for the rest of
the pipeline to use.
