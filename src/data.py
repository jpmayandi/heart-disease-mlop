"""Data loading and cleaning."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "raw" / "heart_raw.csv"
CLEAN_PATH = ROOT / "data" / "processed" / "heart_clean.csv"

NUMERIC_FEATURES = ["age", "trestbps", "chol", "thalach", "oldpeak"]
CATEGORICAL_FEATURES = ["sex", "cp", "fbs", "restecg", "exang", "slope",
                        "ca", "thal"]
FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES
TARGET = "target"


def load_raw(path: Path = RAW_PATH) -> pd.DataFrame:
    return pd.read_csv(path)


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Binarise the target (0 = no disease, 1 = disease) and drop duplicates.

    Missing feature values are left as NaN on purpose: they are imputed inside
    the sklearn Pipeline so that imputation statistics are learned from the
    training folds only (no leakage) and are reused at inference time.
    """
    out = df.copy()
    out[TARGET] = (out[TARGET] > 0).astype(int)
    out = out.drop_duplicates().reset_index(drop=True)
    return out


def save_clean(df: pd.DataFrame, path: Path = CLEAN_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return path


def load_clean(path: Path = CLEAN_PATH) -> pd.DataFrame:
    return pd.read_csv(path)


def split_xy(df: pd.DataFrame):
    return df[FEATURES], df[TARGET]
