import pytest
from fastapi.testclient import TestClient

from tests.test_model import _fit
from sklearn.linear_model import LogisticRegression
import joblib

SAMPLE = {
    "age": 63, "sex": 1, "cp": 1, "trestbps": 145, "chol": 233, "fbs": 1,
    "restecg": 2, "thalach": 150, "exang": 0, "oldpeak": 2.3, "slope": 3,
    "ca": 0, "thal": 6,
}


@pytest.fixture()
def client(tmp_path, monkeypatch):
    pipe, _ = _fit(LogisticRegression(max_iter=500))
    path = tmp_path / "model.joblib"
    joblib.dump(pipe, path)
    monkeypatch.setenv("MODEL_PATH", str(path))
    import api.app as app_module
    with TestClient(app_module.app) as c:
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_predict_returns_prediction_and_confidence(client):
    r = client.post("/predict", json=SAMPLE)
    assert r.status_code == 200
    body = r.json()
    assert body["prediction"] in (0, 1)
    assert 0.5 <= body["confidence"] <= 1.0


def test_predict_rejects_bad_input(client):
    bad = dict(SAMPLE, age=-5)
    assert client.post("/predict", json=bad).status_code == 422


def test_metrics_endpoint_exposes_counters(client):
    client.post("/predict", json=SAMPLE)
    text = client.get("/metrics").text
    assert "api_requests_total" in text
    assert "predictions_total" in text
