"""
Slack alerting for drift detection results.
"""

import os

import requests
from dotenv import load_dotenv

load_dotenv()

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
DRIFT_SHARE_ALERT_THRESHOLD = 0.1


def send_slack_alert(drift_summary: dict):
    """Post a formatted alert to Slack if drift share exceeds threshold."""
    if not SLACK_WEBHOOK_URL:
        print("SLACK_WEBHOOK_URL not set, skipping alert.")
        return

    share = drift_summary["drift_share"]
    if share <= DRIFT_SHARE_ALERT_THRESHOLD:
        print(f"Drift share {share:.2%} below alert threshold, no alert sent.")
        return

    columns_list = "\n".join(
        f"- `{c['column']}` (score: {c['score']:.4f}, threshold: {c['threshold']})"
        for c in drift_summary["drifted_columns"]
    )

    message = {
        "text": (
            f":rotating_light: *Data Drift Detected*\n"
            f"Drift share: *{share:.2%}* "
            f"({drift_summary['drifted_column_count']} columns)\n"
            f"Sample: {drift_summary['n_current_rows']} rows vs "
            f"{drift_summary['n_reference_rows']} reference rows\n\n"
            f"*Drifted columns:*\n{columns_list}\n\n"
            f"_Retrain recommended._"
        )
    }

    resp = requests.post(SLACK_WEBHOOK_URL, json=message, timeout=10)
    resp.raise_for_status()
    print("Slack alert sent.")