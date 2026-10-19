import numpy as np
import pandas as pd

from src import data
from src.preprocess import build_preprocessor


def _toy(n=40):
    rng = np.random.default_rng(0)
    df = pd.DataFrame({
        "age": rng.integers(30, 70, n), "sex": rng.integers(0, 2, n),
        "cp": rng.integers(1, 5, n), "trestbps": rng.integers(100, 180, n),
        "chol": rng.integers(150, 400, n), "fbs": rng.integers(0, 2, n),
        "restecg": rng.integers(0, 3, n), "thalach": rng.integers(90, 190, n),
        "exang": rng.integers(0, 2, n), "oldpeak": rng.uniform(0, 4, n),
        "slope": rng.integers(1, 4, n),
        "ca": rng.choice([0.0, 1.0, np.nan], n),
        "thal": rng.choice([3.0, 7.0, np.nan], n),
        "target": rng.integers(0, 5, n),
    })
    return df


def test_clean_binarises_target():
    out = data.clean(_toy())
    assert set(out[data.TARGET].unique()) <= {0, 1}


def test_clean_removes_duplicates():
    df = _toy()
    dup = pd.concat([df, df.iloc[:5]], ignore_index=True)
    assert len(data.clean(dup)) <= len(data.clean(df))


def test_preprocessor_handles_missing_and_outputs_numeric():
    df = data.clean(_toy())
    X, _ = data.split_xy(df)
    Xt = build_preprocessor().fit_transform(X)
    assert not np.isnan(Xt.toarray() if hasattr(Xt, "toarray") else Xt).any()
    assert Xt.shape[0] == len(df)


def test_preprocessor_unseen_category_ok():
    df = data.clean(_toy())
    X, _ = data.split_xy(df)
    prep = build_preprocessor().fit(X)
    X2 = X.copy()
    X2.loc[X2.index[0], "cp"] = 99
    prep.transform(X2)  # must not raise
