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
            top_shap_contributors TEXT
        )
    """)
    conn.commit()
    conn.close()


def log_prediction(raw_input: dict, fraud_probability: float):
    """Insert one prediction record, without SHAP (computed later on demand)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(
        "INSERT INTO predictions (timestamp, raw_input, fraud_probability, top_shap_contributors) VALUES (?, ?, ?, NULL)",
        (
            datetime.now(timezone.utc).isoformat(),
            json.dumps(raw_input),
            fraud_probability,
        ),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def save_shap_result(prediction_id: int, top_shap_contributors: dict):
    """Cache a computed SHAP result against its prediction, so repeat views don't recompute."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE predictions SET top_shap_contributors = ? WHERE id = ?",
        (json.dumps(top_shap_contributors), prediction_id),
    )
    conn.commit()
    conn.close()


def get_prediction_by_id(prediction_id: int):
    """Fetch one prediction's raw_input, probability, and cached SHAP (if any)."""
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT id, timestamp, raw_input, fraud_probability, top_shap_contributors FROM predictions WHERE id = ?",
        (prediction_id,),
    ).fetchone()
    conn.close()

    if not row:
        return None

    return {
        "id": row[0],
        "timestamp": row[1],
        "raw_input": json.loads(row[2]),
        "fraud_probability": row[3],
        "top_shap_contributors": json.loads(row[4]) if row[4] else None,
    }
    
def get_predictions(limit: int = 50, sort_by_risk: bool = False, offset: int = 0):
    """Fetch a page of predictions, optionally sorted by fraud_probability descending."""
    conn = sqlite3.connect(DB_PATH)
    order = "fraud_probability DESC" if sort_by_risk else "timestamp DESC"
    rows = conn.execute(
        f"SELECT id, timestamp, raw_input, fraud_probability, top_shap_contributors "
        f"FROM predictions ORDER BY {order} LIMIT ? OFFSET ?",
        (limit, offset),
    ).fetchall()
    conn.close()

    return [
        {
            "id": r[0],
            "timestamp": r[1],
            "raw_input": json.loads(r[2]),
            "fraud_probability": r[3],
            "top_shap_contributors": json.loads(r[4]) if r[4] else None,
        }
        for r in rows
    ]


def get_predictions_count():
    """Total number of logged predictions, for pagination controls."""
    conn = sqlite3.connect(DB_PATH)
    count = conn.execute("SELECT COUNT(*) FROM predictions").fetchone()[0]
    conn.close()
    return count