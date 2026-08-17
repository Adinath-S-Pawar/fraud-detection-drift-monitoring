"""
Generate a data drift report comparing logged live traffic (current) against Base.csv (reference), using Evidently.

Run: python -m src.drift_report
"""

import json
import sqlite3

import pandas as pd
from evidently import Report
from evidently.presets import DataDriftPreset

from src import config
from src.data import load_variant
from src.logging_db import DB_PATH


def load_logged_predictions() -> pd.DataFrame:
    """Pull raw_input from every logged prediction, reconstruct as a dataframe.Drops any columns not present 
    in Base (e.g. Variant III/V's synthetic x1/x2 columns)."""
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT raw_input FROM predictions").fetchall()
    conn.close()

    records = [json.loads(r[0]) for r in rows]
    df = pd.DataFrame(records)

    reference_cols = load_variant(config.BASE_VARIANT).drop(columns=[config.TARGET_COL]).columns
    df = df.reindex(columns=reference_cols)  

    return df


def run_drift_report():
    reference = load_variant(config.BASE_VARIANT).drop(columns=[config.TARGET_COL])
    current = load_logged_predictions()

    print(f"Reference (Base) shape: {reference.shape}")
    print(f"Current (logged traffic) shape: {current.shape}")

    report = Report([DataDriftPreset()])
    my_eval = report.run(current, reference)

    my_eval.save_html("drift_report.html")
    print("Saved drift_report.html")

    #inspect the actual structure before parsing it
    result_dict = my_eval.dict()
    with open("drift_report_raw.json", "w") as f:
        json.dump(result_dict, f, indent=2, default=str)
    print("Saved drift_report_raw.json for inspection")


if __name__ == "__main__":
    run_drift_report()