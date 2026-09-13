# Climate data — real, from CIMIS

Station chosen: **CIMIS #262, Linden, San Joaquin County** (~12 mi from
the Lodi/Acampo farm area, elevation 111 ft, active since Feb 2020).

Why this one, not something closer on the map:
- The actual "Lodi" (#42) and "Lodi West" (#166) CIMIS stations exist in
  the historical record but were decommissioned in 2001 and 2015
  respectively — no data available for 2024 or later.
- The next-nearest *active* stations after Linden (Staten Island, Holt,
  Ryde) are all low-lying Sacramento Delta islands (elevation at or below
  sea level) with a cooler, foggier, more maritime-influenced microclimate
  than the Lodi/Acampo growing area — not representative.
- Linden is upland Valley floor, San Joaquin County, closest active match.

If a closer/better station becomes available (CIMIS reactivates Lodi
West, or a private weather station on the farm itself gets added), update
`CIMIS_STATION_ID` in `.env` and re-run `ingestion/cimis_client.py` — the
rest of the pipeline doesn't care which station ID the data came from.

Nothing in this folder is fabricated — see `data/README.md` for the full
data provenance rules across the project.
