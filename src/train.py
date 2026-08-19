"""
Train an XGBoost fraud classifier on BAF's Base variant, tuned via Optuna,
with a SHAP explainer for later use in the API and dashboard.
"""

import json
import time

import optuna
import shap
import xgboost as xgb
from sklearn.metrics import average_precision_score, roc_auc_score
import joblib

from src import config
from src.data import load_and_split_base

import re 

def objective(trial, X_train, y_train, X_val, y_val):
    params = {
        "objective": "binary:logistic",
        "eval_metric": "aucpr",  # PR-AUC — fraud is ~1% positive class
        "tree_method": "hist",
        "max_depth": trial.suggest_int("max_depth", 3, 10),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        "n_estimators": trial.suggest_int("n_estimators", 100, 800),
        "subsample": trial.suggest_float("subsample", 0.5, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
        "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
        "gamma": trial.suggest_float("gamma", 0, 5),
        "reg_alpha": trial.suggest_float("reg_alpha", 1e-3, 10, log=True),
        "reg_lambda": trial.suggest_float("reg_lambda", 1e-3, 10, log=True),
        "scale_pos_weight": trial.suggest_float("scale_pos_weight", 1, 50),
        "random_state": config.RANDOM_STATE,
    }

    model = xgb.XGBClassifier(**params, early_stopping_rounds=30)
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    preds = model.predict_proba(X_val)[:, 1]
    return average_precision_score(y_val, preds)


def cleanup_old_versions(keep_last: int = 3):
    """Delete versioned model artifacts beyond the most recent `keep_last` versions."""
    pattern = re.compile(r"xgb_fraud_model_v(\d+)\.json$")
    versions_found = []

    for f in config.MODEL_DIR.glob("xgb_fraud_model_v*.json"):
        match = pattern.search(f.name)
        if match:
            versions_found.append(int(match.group(1)))

    versions_found = sorted(set(versions_found), reverse=True)
    to_delete = versions_found[keep_last:]

    for v in to_delete:
        paths = config.get_versioned_paths(f"v{v}")
        for path in paths.values():
            if path.exists():
                path.unlink()
        print(f"Removed old version v{v} artifacts")


def train(version: str = "v1"):
    paths = config.get_versioned_paths(version)
    print(f"Loading and preprocessing Base variant... (training {version})")
    X_train, X_val, y_train, y_val, feature_names = load_and_split_base(
        preprocessor_path=paths["preprocessor"],
        feature_names_path=paths["feature_names"],
        missing_medians_path=paths["missing_medians"],
    )
    print(f"Train shape: {X_train.shape}, Val shape: {X_val.shape}")

    print(f"\nRunning Optuna tuning ({config.N_OPTUNA_TRIALS} trials)...")
    study = optuna.create_study(direction="maximize")
    start = time.time()
    study.optimize(
        lambda trial: objective(trial, X_train, y_train, X_val, y_val),
        n_trials=config.N_OPTUNA_TRIALS,
        timeout=config.OPTUNA_TIMEOUT_SECONDS,
    )
    print(f"Tuning done in {time.time() - start:.1f}s. Best PR-AUC: {study.best_value:.4f}")

    print("\nTraining final model on best params...")
    best_params = {
        **study.best_params,
        "objective": "binary:logistic",
        "eval_metric": "aucpr",
        "tree_method": "hist",
        "random_state": config.RANDOM_STATE,
    }
    final_model = xgb.XGBClassifier(**best_params, early_stopping_rounds=30)
    final_model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)

    val_probs = final_model.predict_proba(X_val)[:, 1]
    roc_auc = roc_auc_score(y_val, val_probs)
    pr_auc = average_precision_score(y_val, val_probs)
    print(f"\nROC-AUC: {roc_auc:.4f} | PR-AUC: {pr_auc:.4f}")

    metrics = {
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        "best_optuna_params": study.best_params,
        "n_trials_run": len(study.trials),
    }
    with open(paths["metrics"], "w") as f:
        json.dump(metrics, f, indent=2)

    final_model.save_model(paths["model"])
    print(f"Model saved to {paths["model"]}")

    print("Building SHAP TreeExplainer...")
    explainer = shap.TreeExplainer(final_model)
    joblib.dump(explainer, paths["shap_explainer"])
    print(f"SHAP explainer saved to {paths["shap_explainer"]}")
    
    cleanup_old_versions(keep_last=3)


if __name__ == "__main__":
    import sys
    version = sys.argv[1] if len(sys.argv) > 1 else "v1"
    train(version)
