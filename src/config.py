"""
Central config for the Fraud/Credit Risk Detection + Drift Monitoring.
"""

from pathlib import Path

# ---- Paths ----
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
MODEL_DIR = PROJECT_ROOT / "models"

# ---- Missing-value handling ----
MISSING_INDICATOR_COLS = ["prev_address_months_count", "bank_months_count"]
MISSING_MEDIANS_PATH = MODEL_DIR / "missing_medians.json"

MODEL_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

# ---- Dataset variants ----
BASE_VARIANT = "Base.csv"
DRIFT_VARIANTS = [
    "Variant I.csv",
    "Variant II.csv",
    "Variant III.csv",
    "Variant IV.csv",
    "Variant V.csv",
]

TARGET_COL = "fraud_bool"

# ---- Train/val split ----
TEST_SIZE = 0.2
RANDOM_STATE = 42

# ---- Model artifact names ----
MODEL_PATH = MODEL_DIR / "xgb_fraud_model.json" 
PREPROCESSOR_PATH = MODEL_DIR / "preprocessor.joblib"
FEATURE_NAMES_PATH = MODEL_DIR / "feature_names.json"
SHAP_EXPLAINER_PATH = MODEL_DIR / "shap_explainer.joblib"
METRICS_PATH = MODEL_DIR / "training_metrics.json"

# ---- Optuna ----
N_OPTUNA_TRIALS = 3 # bump for final run — kept low during local dev on limited hardware
OPTUNA_TIMEOUT_SECONDS = 600 #10min

# ---- Model versioning (for retrain trigger) ----
def get_versioned_paths(version: str):
    """Return artifact paths for a specific model version, e.g. 'v1', 'v2'."""
    return {
        "model": MODEL_DIR / f"xgb_fraud_model_{version}.json",
        "preprocessor": MODEL_DIR / f"preprocessor_{version}.joblib",
        "feature_names": MODEL_DIR / f"feature_names_{version}.json",
        "shap_explainer": MODEL_DIR / f"shap_explainer_{version}.joblib",
        "metrics": MODEL_DIR / f"training_metrics_{version}.json",
        "missing_medians": MODEL_DIR / f"missing_medians_{version}.json",
    }

CURRENT_VERSION_FILE = MODEL_DIR / "current_version.txt"

# ---- Drift status cache (avoids recomputing on every dashboard read) ----
DRIFT_STATUS_CACHE_PATH = MODEL_DIR.parent / "drift_status_latest.json"