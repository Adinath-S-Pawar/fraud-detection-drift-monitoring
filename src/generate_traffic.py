"""
Send rows from a BAF variant through the running /predict endpoint, to
populate predictions.db with realistic "live traffic" for drift analysis.

Run the API first (python -m src.api), then in a second terminal:
    python -m src.generate_traffic "Variant I.csv" 500
"""

import sys

import requests

from src import config
from src.data import load_variant

API_URL = "http://localhost:8000/predict"


def send_traffic(filename: str, n_rows: int):
    df = load_variant(filename)
    sample = df.drop(columns=[config.TARGET_COL]).sample(
        n=min(n_rows, len(df)), random_state=config.RANDOM_STATE
    )

    sent, failed = 0, 0
    for _, row in sample.iterrows():
        payload = row.to_dict()
        try:
            resp = requests.post(API_URL, json=payload, timeout=5)
            resp.raise_for_status()
            sent += 1
        except requests.RequestException as e:
            failed += 1
            if failed <= 3:  # avoiding flooding console
                print(f"Request failed: {e}")

        if sent % 100 == 0 and sent > 0:
            print(f"{sent}/{n_rows} sent...")

    print(f"\nDone. Sent: {sent}, Failed: {failed}")


if __name__ == "__main__":
    filename = sys.argv[1] if len(sys.argv) > 1 else "Variant I.csv"
    n_rows = int(sys.argv[2]) if len(sys.argv) > 2 else 500
    send_traffic(filename, n_rows)