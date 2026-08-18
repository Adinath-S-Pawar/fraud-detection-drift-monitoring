"""
Loading + preprocessing for the BAF dataset suite.
"""

import json
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
import joblib

from src import config

def load_variant(filename: str) -> pd.DataFrame:
    """Load a BAF CSV from data/ by filename."""
    path = config.DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"{path} not found.")
    return pd.read_csv(path)

def get_feature_types(df: pd.DataFrame):
    """Split feature columns into (numeric, categorical)"""
    features = [c for c in df.columns if c != config.TARGET_COL]
    numeric = [c for c in features if pd.api.types.is_numeric_dtype(df[c])]
    categorical = [c for c in features if c not in numeric]
    return numeric, categorical

def handle_missing_sentinels(df: pd.DataFrame, medians: dict | None = None):
    """Replace -1 sentinel (missing) with median of real values, add a 
    binary was_missing flag per column. """
    df = df.copy()
    computed_medians = {}

    for col in config.MISSING_INDICATOR_COLS:
        df[f"{col}_was_missing"] = (df[col] == -1).astype(int)

        if medians is None:
            real_values = df.loc[df[col] != -1, col]
            median = real_values.median()
            computed_medians[col] = median
        else:
            median = medians[col]

        df[col] = df[col].replace(-1, median)

    return df, (medians if medians is not None else computed_medians)

def build_preprocessor(df: pd.DataFrame) -> ColumnTransformer:
    """Scale numeric columns, one-hot encode categorical columns."""
    numeric, categorical = get_feature_types(df)
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric),
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical),
        ]
    )

def load_and_split_base(preprocessor_path=None, feature_names_path=None, missing_medians_path=None):
    """Load Base.csv, split 80/20 stratified, fit preprocessor on train only, save artifacts."""
    preprocessor_path = preprocessor_path or config.PREPROCESSOR_PATH
    feature_names_path = feature_names_path or config.FEATURE_NAMES_PATH
    missing_medians_path = missing_medians_path or config.MISSING_MEDIANS_PATH
    
    df = load_variant(config.BASE_VARIANT)
    y = df[config.TARGET_COL]
    X = df.drop(columns=[config.TARGET_COL])

    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=config.TEST_SIZE, random_state=config.RANDOM_STATE, stratify=y,
    )

    X_train, medians = handle_missing_sentinels(X_train)
    X_val, _ = handle_missing_sentinels(X_val, medians=medians)

    with open(missing_medians_path, "w") as f:
        json.dump(medians, f)

    preprocessor = build_preprocessor(X_train)
    X_train_t = preprocessor.fit_transform(X_train)
    X_val_t = preprocessor.transform(X_val)

    joblib.dump(preprocessor, preprocessor_path)

    feature_names = preprocessor.get_feature_names_out().tolist()
    with open(feature_names_path, "w") as f:
        json.dump(feature_names, f)

    return X_train_t, X_val_t, y_train, y_val, feature_names