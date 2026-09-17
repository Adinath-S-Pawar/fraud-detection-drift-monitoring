"""
Send rows from a BAF variant through a running /predict endpoint, to
populate predictions.db with realistic "live traffic" for drift analysis.

Run against local API:
    python -m src.generate_traffic "Variant I.csv" 500

Run against a deployed API:
    python -m src.generate_traffic "Variant I.csv" 500 https://fraud-detection-drift-monitoring.onrender.com
"""

import sys

import requests

from src import config
from src.data import load_variant
import os
from dotenv import load_dotenv
load_dotenv()

ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")

DEFAULT_API_URL = "http://localhost:8000"


def send_traffic(filename: str, n_rows: int, base_url: str = DEFAULT_API_URL):
    predict_url = f"{base_url}/predict"
    df = load_variant(filename)
    sample = df.drop(columns=[config.TARGET_COL]).sample(n=min(n_rows, len(df)))

    sent, failed = 0, 0
    for _, row in sample.iterrows():
        payload = row.to_dict()
        try:
            headers = {"X-API-Key": ADMIN_API_KEY}
            resp = requests.post(predict_url, json=payload, headers=headers, timeout=15)
            resp.raise_for_status()
            sent += 1
        except requests.RequestException as e:
            failed += 1
            if failed <= 3:
                print(f"Request failed: {e}")

        if sent % 20 == 0 and sent > 0:
            print(f"{sent}/{n_rows} sent...")

    print(f"\nDone. Target: {base_url} | Sent: {sent}, Failed: {failed}")


if __name__ == "__main__":
    filename = sys.argv[1] if len(sys.argv) > 1 else "Variant I.csv"
    n_rows = int(sys.argv[2]) if len(sys.argv) > 2 else 500
    base_url = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_API_URL
    send_traffic(filename, n_rows, base_url)