"""
FastAPI service for fraud prediction. Loads the trained model + preprocessor
at startup, exposes /predict, and logs predictions for drift monitoring.
"""

import json

import joblib
import pandas as pd
import shap
import xgboost as xgb
from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict

from src import config

app = FastAPI(title="Fraud Detection API")

# ---- Load artifacts once at startup, not per-request ----
model = xgb.XGBClassifier()
model.load_model(config.MODEL_PATH)

preprocessor = joblib.load(config.PREPROCESSOR_PATH)
explainer = joblib.load(config.SHAP_EXPLAINER_PATH)

with open(config.FEATURE_NAMES_PATH) as f:
    feature_names = json.load(f)


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
    transformed = preprocessor.transform(raw)

    proba = model.predict_proba(transformed)[0][1]

    shap_values = explainer.shap_values(transformed)
    contributions = dict(zip(feature_names, shap_values[0].tolist()))
    top_contributors = dict(
        sorted(contributions.items(), key=lambda x: abs(x[1]), reverse=True)[:5]
    )

    return {
        "fraud_probability": float(proba),
        "top_shap_contributors": top_contributors,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api:app", host="0.0.0.0", port=8000, reload=True)