import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from src import data
from src.preprocess import build_preprocessor
from tests.test_data import _toy


def _fit(est):
    df = data.clean(_toy(80))
    X, y = data.split_xy(df)
    pipe = Pipeline([("prep", build_preprocessor()), ("clf", est)])
    return pipe.fit(X, y), X


def test_logreg_pipeline_predicts_probabilities():
    pipe, X = _fit(LogisticRegression(max_iter=500))
    proba = pipe.predict_proba(X)
    assert proba.shape == (len(X), 2)
    assert np.allclose(proba.sum(axis=1), 1.0)


def test_rf_pipeline_predicts_binary():
    pipe, X = _fit(RandomForestClassifier(n_estimators=10, random_state=0))
    assert set(pipe.predict(X)) <= {0, 1}


def test_model_roundtrip_joblib(tmp_path):
    pipe, X = _fit(LogisticRegression(max_iter=500))
    path = tmp_path / "m.joblib"
    joblib.dump(pipe, path)
    loaded = joblib.load(path)
    assert np.allclose(pipe.predict_proba(X), loaded.predict_proba(X))
