"""
Cleans a raw tab-delimited sensor export (as downloaded from the Google Sheet
the ESP32 stations post to) into data/raw/sensordata.csv.

Handles two quirks seen in real exports from this project:
  - trailing empty spreadsheet columns beyond the 8 named fields
  - trailing blank rows at the end of the export

Run again any time a new export is dropped in — it re-derives the full
cleaned CSV from the raw export(s) rather than appending, so it's safe to
re-run.

Usage:
    python ingestion/clean_raw_export.py path/to/export1.txt [path/to/export2.txt ...]
"""

import csv
import sys
from pathlib import Path

import pandas as pd

COLUMNS = [
    "timestamp",
    "station",
    "soil_moisture_1",
    "soil_moisture_2",
    "air_temp",
    "humidity",
    "soil_temp",
    "light_lux",
]

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = REPO_ROOT / "data" / "raw" / "sensordata.csv"


def load_export(path: Path) -> pd.DataFrame:
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        header = next(reader)
        assert [h.strip() for h in header[: len(COLUMNS)]] == COLUMNS, (
            f"Unexpected header in {path}: {header[:len(COLUMNS)]}"
        )
        for row in reader:
            if not row or row[0].strip() == "":
                continue  # trailing blank row
            trimmed = (row + [""] * len(COLUMNS))[: len(COLUMNS)]
            rows.append(trimmed)
    return pd.DataFrame(rows, columns=COLUMNS)


def main(export_paths: list[str]) -> None:
    if not export_paths:
        raise SystemExit("Usage: clean_raw_export.py <export.txt> [more exports...]")

    frames = [load_export(Path(p)) for p in export_paths]
    df = pd.concat(frames, ignore_index=True)

    df["timestamp"] = pd.to_datetime(df["timestamp"], format="%m/%d/%Y %H:%M:%S")
    numeric_cols = [
        "soil_moisture_1",
        "soil_moisture_2",
        "air_temp",
        "humidity",
        "soil_temp",
        "light_lux",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col].replace("", pd.NA))

    df = df.sort_values(["station", "timestamp"]).drop_duplicates(
        subset=["station", "timestamp"]
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"Wrote {len(df)} rows to {OUTPUT_PATH}")
    print(df["station"].value_counts())


if __name__ == "__main__":
    main(sys.argv[1:])
