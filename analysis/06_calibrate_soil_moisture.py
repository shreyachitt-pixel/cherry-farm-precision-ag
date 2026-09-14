"""
Runs the real soil-moisture sensor calibration: reads gravimetric samples
(see data/calibration/README.md for the physical protocol), computes real
volumetric water content per sample, fits raw-ADC -> VWC in three candidate
forms, and saves the best-supported one for the rest of the pipeline.

Run:
    ./venv/bin/python analysis/06_calibrate_soil_moisture.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from models.soil_moisture_calibration import compute_sample_moisture, select_best_fit

DATA_PATH = REPO_ROOT / "data" / "calibration" / "soil_moisture_calibration.csv"
TEMPLATE_PATH = REPO_ROOT / "data" / "calibration" / "soil_moisture_calibration_TEMPLATE.csv"
OUTPUT_JSON = REPO_ROOT / "data" / "calibration" / "fitted_calibration.json"
OUTPUT_PLOT = REPO_ROOT / "visualizations" / "03_soil_moisture_calibration.png"

REQUIRED_COLS = ["raw_adc", "container_volume_cm3", "container_tare_g", "gross_wet_mass_g", "gross_dry_mass_g"]


def load_filled_samples() -> pd.DataFrame:
    if not DATA_PATH.exists():
        raise SystemExit(
            f"{DATA_PATH} not found.\n"
            f"Copy {TEMPLATE_PATH.name} to {DATA_PATH.name} and fill it in with real "
            "gravimetric samples first -- see data/calibration/README.md for the protocol."
        )
    df = pd.read_csv(DATA_PATH)
    missing = df[REQUIRED_COLS].isna().any(axis=1)
    if missing.any():
        raise SystemExit(
            f"{missing.sum()} row(s) in {DATA_PATH.name} still have blank measurements "
            f"(rows: {list(df[missing]['sample_id'])}). Fill in every row before running this."
        )
    return df


def main() -> None:
    df = load_filled_samples()

    moisture = df.apply(
        lambda r: compute_sample_moisture(
            gross_wet_mass_g=r["gross_wet_mass_g"],
            gross_dry_mass_g=r["gross_dry_mass_g"],
            container_tare_g=r["container_tare_g"],
            container_volume_cm3=r["container_volume_cm3"],
        ),
        axis=1,
    )
    df["gwc"] = [m.gwc for m in moisture]
    df["bulk_density_g_cm3"] = [m.bulk_density for m in moisture]
    df["vwc"] = [m.vwc for m in moisture]

    calibrations = {}
    fig, axes = plt.subplots(1, df["sensor_channel"].nunique(), figsize=(6 * df["sensor_channel"].nunique(), 5), squeeze=False)

    for i, (channel, sub) in enumerate(df.groupby("sensor_channel")):
        print(f"=== {channel} ({len(sub)} samples) ===")
        adc = sub["raw_adc"].to_numpy()
        vwc = sub["vwc"].to_numpy()

        if len(sub) < 2:
            print("  Need at least 2 samples to fit anything -- skipping.")
            continue

        best, candidates = select_best_fit(adc, vwc)
        for c in candidates:
            marker = " <- selected" if c is best else ""
            print(f"  {c.form:16s} R^2={c.r_squared:.4f}  adj.R^2={c.adjusted_r_squared:.4f}{marker}")

        calibrations[channel] = {
            "form": best.form,
            "coefficients": best.coefficients,
            "r_squared": best.r_squared,
            "adjusted_r_squared": best.adjusted_r_squared,
            "n_samples": best.n_samples,
        }

        ax = axes[0][i]
        ax.scatter(adc, vwc, label="real gravimetric samples")
        x_line = np.linspace(adc.min(), adc.max(), 100)
        y_line = [best.predict(x) for x in x_line]
        ax.plot(x_line, y_line, color="tab:orange", label=f"{best.form} fit (R^2={best.r_squared:.3f})")
        ax.set_xlabel("Raw ADC")
        ax.set_ylabel("Volumetric water content (cm3/cm3)")
        ax.set_title(channel)
        ax.legend()
        print()

    OUTPUT_JSON.write_text(json.dumps(calibrations, indent=2))
    print(f"Saved fitted calibration to {OUTPUT_JSON}")

    OUTPUT_PLOT.parent.mkdir(exist_ok=True)
    fig.tight_layout()
    fig.savefig(OUTPUT_PLOT, dpi=130)
    print(f"Saved plot to {OUTPUT_PLOT}")


if __name__ == "__main__":
    main()
