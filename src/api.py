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
from src.logging_db import init_db, log_prediction

app = FastAPI(title="Fraud Detection API")

init_db()

# ---- Load artifacts once at startup, not per-request ----
model = xgb.XGBClassifier()
model.load_model(config.MODEL_PATH)

preprocessor = joblib.load(config.PREPROCESSOR_PATH)
explainer = joblib.load(config.SHAP_EXPLAINER_PATH)

with open(config.FEATURE_NAMES_PATH) as f:
    feature_names = json.load(f)

with open(config.MISSING_MEDIANS_PATH) as f:
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api:app", host="0.0.0.0", port=8000, reload=True)