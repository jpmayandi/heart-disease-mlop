"""Generate a synthetic stand-in with the same schema as the UCI dataset.

ONLY for offline smoke tests / CI when the real download is unavailable.
Real runs should use scripts/download_data.py.
"""
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parents[1] / "data" / "raw" / "heart_raw.csv"


def main(n: int = 303, seed: int = 42) -> None:
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({
        "age": rng.integers(29, 78, n),
        "sex": rng.integers(0, 2, n),
        "cp": rng.integers(1, 5, n),
        "trestbps": rng.integers(94, 200, n),
        "chol": rng.integers(126, 564, n),
        "fbs": rng.integers(0, 2, n),
        "restecg": rng.integers(0, 3, n),
        "thalach": rng.integers(71, 202, n),
        "exang": rng.integers(0, 2, n),
        "oldpeak": np.round(rng.uniform(0, 6, n), 1),
        "slope": rng.integers(1, 4, n),
        "ca": rng.choice([0.0, 1.0, 2.0, 3.0, np.nan], n,
                         p=[.55, .2, .12, .09, .04]),
        "thal": rng.choice([3.0, 6.0, 7.0, np.nan], n, p=[.55, .06, .37, .02]),
    })
    score = (0.04 * df.age + 0.8 * df.exang + 0.6 * df.oldpeak
             + 0.7 * df.cp.eq(4) + 0.6 * df.ca.fillna(0) - 0.02 * df.thalach)
    df["target"] = ((score + rng.normal(0, 0.8, n)) > score.median()).astype(
        int) * rng.integers(1, 5, n) // 1
    df["target"] = df["target"].clip(0, 4)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"Wrote synthetic data -> {OUT}")


if __name__ == "__main__":
    main()
