"""
SQLite logging for predictions. Each row = one scored transaction, used
later by the drift monitoring job as the "live traffic" sample.
"""

import json
import sqlite3
from datetime import datetime, timezone

from src import config

DB_PATH = config.MODEL_DIR.parent / "predictions.db"


def init_db():
    """Create the predictions table if it doesn't exist yet."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            raw_input TEXT NOT NULL,
            fraud_probability REAL NOT NULL,
            top_shap_contributors TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def log_prediction(raw_input: dict, fraud_probability: float, top_shap_contributors: dict):
    """Insert one prediction record."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO predictions (timestamp, raw_input, fraud_probability, top_shap_contributors) VALUES (?, ?, ?, ?)",
        (
            datetime.now(timezone.utc).isoformat(),
            json.dumps(raw_input),
            fraud_probability,
            json.dumps(top_shap_contributors),
        ),
    )
    conn.commit()
    conn.close()