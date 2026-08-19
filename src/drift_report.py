"""
Data drift detection: compares logged live traffic (current) against Base.csv (reference) using Evidently, 
and exposes a structured summary for use by the scheduled job and alerting.
"""

import json
import sqlite3

import pandas as pd
from evidently import Report
from evidently.presets import DataDriftPreset

from src import config
from src.data import load_variant
from src.logging_db import DB_PATH
from src.alerting import send_slack_alert
from datetime import datetime, timezone


def load_logged_predictions() -> pd.DataFrame:
    """Pull raw_input from every logged prediction, reconstruct as a dataframe.
    Drops any columns not present in Base """
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT raw_input FROM predictions").fetchall()
    conn.close()

    records = [json.loads(r[0]) for r in rows]
    df = pd.DataFrame(records)

    reference_cols = load_variant(config.BASE_VARIANT).drop(columns=[config.TARGET_COL]).columns
    df = df.reindex(columns=reference_cols)

    return df


def get_drift_summary(save_html: bool = True) -> dict:
    """Run the drift report, return a structured summary."""
    reference = load_variant(config.BASE_VARIANT).drop(columns=[config.TARGET_COL])
    current = load_logged_predictions()

    report = Report([DataDriftPreset()])
    my_eval = report.run(current, reference)

    if save_html:
        my_eval.save_html("drift_report.html")

    result = my_eval.dict()
    metrics = result["metrics"]

    dataset_summary = metrics[0]["value"]

    drifted_columns = []
    for m in metrics[1:]:
        threshold = m["config"].get("threshold", 0.1)
        if m["value"] > threshold:
            col_name = m["metric_name"].split("column=")[1].split(",")[0]
            drifted_columns.append({
                "column": col_name,
                "score": m["value"],
                "threshold": threshold,
            })

    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "n_reference_rows": len(reference),
        "n_current_rows": len(current),
        "drift_share": dataset_summary["share"],
        "drifted_column_count": dataset_summary["count"],
        "drifted_columns": drifted_columns,
    }

    with open(config.DRIFT_STATUS_CACHE_PATH, "w") as f:
        json.dump(summary, f, indent=2)

    return summary


if __name__ == "__main__":
    summary = get_drift_summary()
    print(json.dumps(summary, indent=2))
    send_slack_alert(summary)