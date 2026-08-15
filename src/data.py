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
    path = config.DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"{path} not found.")
    return pd.read_csv(path)

def get_feature_types(df: pd.DataFrame):
    features = [c for c in df.columns if c != config.TARGET_COL]
    numeric = [c for c in features if pd.api.types.is_numeric_dtype(df[c])]
    categorical = [c for c in features if c not in numeric]
    return numeric, categorical


def build_preprocessor(df: pd.DataFrame) -> ColumnTransformer:
    numeric, categorical = get_feature_types(df)
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric),
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical),
        ]
    )


def load_and_split_base():
    """Load Base.csv, fit preprocessor on train split only, return train/val splits."""
    df = load_variant(config.BASE_VARIANT)
    y = df[config.TARGET_COL]
    X = df.drop(columns=[config.TARGET_COL])

    X_train, X_val, y_train, y_val = train_test_split(
        X, y,
        test_size=config.TEST_SIZE,
        random_state=config.RANDOM_STATE,
        stratify=y,
    )

    preprocessor = build_preprocessor(X_train)
    X_train_t = preprocessor.fit_transform(X_train)
    X_val_t = preprocessor.transform(X_val)

    joblib.dump(preprocessor, config.PREPROCESSOR_PATH)

    feature_names = preprocessor.get_feature_names_out().tolist()
    with open(config.FEATURE_NAMES_PATH, "w") as f:
        json.dump(feature_names, f)

    return X_train_t, X_val_t, y_train, y_val, feature_names