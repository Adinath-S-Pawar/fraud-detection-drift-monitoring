"""
FastAPI service for fraud prediction. Loads the trained model + preprocessor
at startup, exposes /predict, and logs predictions for drift monitoring.
"""

import json

import joblib
import pandas as pd
import xgboost as xgb
from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict

from src import config
from src.data import handle_missing_sentinels
from src.logging_db import init_db, log_prediction, get_predictions
from src.drift_report import get_drift_summary

app = FastAPI(title="Fraud Detection API")

init_db()

# ---- Load whichever version current_version.txt points to ----
with open(config.CURRENT_VERSION_FILE) as f:
    live_version = f.read().strip()

paths = config.get_versioned_paths(live_version)
print(f"Loading model version: {live_version}")

model = xgb.XGBClassifier()
model.load_model(paths["model"])

preprocessor = joblib.load(paths["preprocessor"])
explainer = joblib.load(paths["shap_explainer"])

with open(paths["feature_names"]) as f:
    feature_names = json.load(f)

with open(paths["missing_medians"]) as f:
    missing_medians = json.load(f)


class Transaction(BaseModel):
    """Raw transaction fields — accepts any extra fields, only known columns get used."""
    model_config = ConfigDict(extra="allow")


@app.get("/health")
def health():
    """Basic liveness check."""
    return {"status": "ok"}


@app.post("/predict")
def predict(transaction: Transaction):
    """Score a single transaction, return fraud probability + top SHAP contributors."""
    raw = pd.DataFrame([transaction.model_dump()])
    raw, _ = handle_missing_sentinels(raw, medians=missing_medians)

    transformed = preprocessor.transform(raw)
    proba = model.predict_proba(transformed)[0][1]

    shap_values = explainer.shap_values(transformed)
    contributions = dict(zip(feature_names, shap_values[0].tolist()))
    top_contributors = dict(
        sorted(contributions.items(), key=lambda x: abs(x[1]), reverse=True)[:5]
    )
    
    log_prediction(
        raw_input=transaction.model_dump(),
        fraud_probability=float(proba),
        top_shap_contributors=top_contributors,
    )

    return {
        "fraud_probability": float(proba),
        "top_shap_contributors": top_contributors,
    }

@app.get("/predictions")
def predictions(limit: int = 50, sort_by_risk: bool = False):
    """Recent logged predictions, for the dashboard's live predictions table."""
    return get_predictions(limit=limit, sort_by_risk=sort_by_risk)


@app.get("/drift-status")
def drift_status():
    """Latest cached drift check result, for the dashboard's drift panel."""
    if not config.DRIFT_STATUS_CACHE_PATH.exists():
        return {"error": "No drift check has run yet."}

    with open(config.DRIFT_STATUS_CACHE_PATH) as f:
        return json.load(f)


@app.get("/model-info")
def model_info():
    """Currently live model version and its training metrics."""
    with open(config.CURRENT_VERSION_FILE) as f:
        version = f.read().strip()

    paths = config.get_versioned_paths(version)
    with open(paths["metrics"]) as f:
        metrics = json.load(f)

    return {
        "live_version": version,
        "roc_auc": metrics["roc_auc"],
        "pr_auc": metrics["pr_auc"],
    }
    
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api:app", host="0.0.0.0", port=8000, reload=True)