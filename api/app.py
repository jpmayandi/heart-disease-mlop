"""FastAPI model-serving app with logging and Prometheus metrics."""
import logging
import os
import time
from pathlib import Path

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException, Request, Response
from prometheus_client import (CONTENT_TYPE_LATEST, Counter, Gauge, Histogram,
                               generate_latest)
from pydantic import BaseModel, Field

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("heart-api")

DEFAULT_MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / \
    "model.joblib"

REQUESTS = Counter("api_requests_total", "Total API requests",
                   ["method", "endpoint", "status"])
LATENCY = Histogram("api_request_latency_seconds", "Request latency",
                    ["endpoint"])
PREDICTIONS = Counter("predictions_total", "Predictions by class",
                      ["prediction"])
CONFIDENCE = Histogram("prediction_confidence", "Model confidence",
                       buckets=[.5, .6, .7, .8, .9, 1.0])
MODEL_LOADED = Gauge("model_loaded", "1 if model is loaded")

app = FastAPI(title="Heart Disease Risk API", version="1.0.0")
model = None


class PatientData(BaseModel):
    age: float = Field(..., ge=1, le=120)
    sex: int = Field(..., ge=0, le=1)
    cp: int = Field(..., ge=1, le=4)
    trestbps: float = Field(..., gt=0)
    chol: float = Field(..., gt=0)
    fbs: int = Field(..., ge=0, le=1)
    restecg: int = Field(..., ge=0, le=2)
    thalach: float = Field(..., gt=0)
    exang: int = Field(..., ge=0, le=1)
    oldpeak: float = Field(..., ge=0)
    slope: int = Field(..., ge=1, le=3)
    ca: float = Field(0, ge=0, le=4)
    thal: float = Field(3, ge=0, le=7)


@app.on_event("startup")
def load_model() -> None:
    global model
    path = Path(os.getenv("MODEL_PATH", DEFAULT_MODEL_PATH))
    model = joblib.load(path)
    MODEL_LOADED.set(1)
    logger.info("Model loaded from %s", path)


@app.middleware("http")
async def track(request: Request, call_next):
    start = time.perf_counter()
    status = 500
    try:
        response = await call_next(request)
        status = response.status_code
        return response
    finally:
        elapsed = time.perf_counter() - start
        path = request.url.path
        if path != "/metrics":
            REQUESTS.labels(request.method, path, str(status)).inc()
            LATENCY.labels(path).observe(elapsed)
            logger.info("%s %s -> %s (%.1f ms)", request.method, path,
                        status, elapsed * 1000)


@app.get("/")
def root():
    return {"service": "heart-disease-api", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok" if model is not None else "model_not_loaded"}


@app.post("/predict")
def predict(patient: PatientData):
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    row = pd.DataFrame([patient.model_dump()])
    proba = float(model.predict_proba(row)[0, 1])
    pred = int(proba >= 0.5)
    confidence = proba if pred == 1 else 1 - proba
    PREDICTIONS.labels(str(pred)).inc()
    CONFIDENCE.observe(confidence)
    logger.info("prediction=%s confidence=%.3f input=%s", pred, confidence,
                patient.model_dump())
    return {
        "prediction": pred,
        "label": "heart disease" if pred else "no heart disease",
        "confidence": round(confidence, 4),
        "probability_disease": round(proba, 4),
    }


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
