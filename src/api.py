"""
FastAPI service for fraud prediction. Loads the trained model + preprocessor
at startup, exposes /predict, and logs predictions for drift monitoring.
"""

from fastapi import FastAPI

app = FastAPI(title="Fraud Detection API")


@app.get("/health")
def health():
    """Basic liveness check."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api:app", host="0.0.0.0", port=8000, reload=True)