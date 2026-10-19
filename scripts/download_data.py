"""Download the UCI Heart Disease (Cleveland) dataset and save a raw CSV.

Usage:
    python scripts/download_data.py            # saves data/raw/heart_raw.csv

Tries the direct UCI URL first, then falls back to the `ucimlrepo` package.
"""
import io
import sys
from pathlib import Path

import pandas as pd
import requests

URL = (
    "https://archive.ics.uci.edu/ml/machine-learning-databases/"
    "heart-disease/processed.cleveland.data"
)
COLUMNS = [
    "age", "sex", "cp", "trestbps", "chol", "fbs", "restecg",
    "thalach", "exang", "oldpeak", "slope", "ca", "thal", "target",
]
OUT = Path(__file__).resolve().parents[1] / "data" / "raw" / "heart_raw.csv"


def from_url() -> pd.DataFrame:
    resp = requests.get(URL, timeout=30)
    resp.raise_for_status()
    return pd.read_csv(io.StringIO(resp.text), header=None, names=COLUMNS,
                       na_values="?")


def from_ucimlrepo() -> pd.DataFrame:
    from ucimlrepo import fetch_ucirepo  # pip install ucimlrepo

    ds = fetch_ucirepo(id=45)
    df = ds.data.features.copy()
    df["target"] = ds.data.targets.values.ravel()
    return df[COLUMNS]


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    try:
        df = from_url()
        print("Downloaded from UCI URL")
    except Exception as exc:  # noqa: BLE001
        print(f"Direct download failed ({exc}); trying ucimlrepo ...")
        df = from_ucimlrepo()
    df.to_csv(OUT, index=False)
    print(f"Saved {len(df)} rows x {df.shape[1]} cols -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
