"""
Central config for the Fraud/Credit Risk Detection + Drift Monitoring.
"""

from pathlib import Path

# ---- Paths ----
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
MODEL_DIR = PROJECT_ROOT / "models"

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
N_OPTUNA_TRIALS = 40
OPTUNA_TIMEOUT_SECONDS = 1800