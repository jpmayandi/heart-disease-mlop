"""Train Logistic Regression and Random Forest, track with MLflow, save best.

Usage:
    python -m src.train
"""
import json
import os
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import mlflow  # noqa: E402
import mlflow.sklearn  # noqa: E402
import numpy as np  # noqa: E402
from sklearn.ensemble import RandomForestClassifier  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import (ConfusionMatrixDisplay, RocCurveDisplay,  # noqa
                             accuracy_score, f1_score, precision_score,
                             recall_score, roc_auc_score)
from sklearn.model_selection import (GridSearchCV, StratifiedKFold,  # noqa
                                     cross_validate, train_test_split)
from sklearn.pipeline import Pipeline  # noqa: E402

from src import data  # noqa: E402
from src.preprocess import build_preprocessor  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = ROOT / "models"
FIG_DIR = ROOT / "reports" / "figures"
EXPERIMENT = "heart-disease-classification"
SEED = 42

CANDIDATES = {
    "logistic_regression": (
        LogisticRegression(max_iter=2000, random_state=SEED),
        {"clf__C": [0.01, 0.1, 1, 10], "clf__penalty": ["l2"]},
    ),
    "random_forest": (
        RandomForestClassifier(random_state=SEED),
        {"clf__n_estimators": [100, 300],
         "clf__max_depth": [3, 5, None],
         "clf__min_samples_leaf": [1, 3]},
    ),
}


def evaluate(model, X, y):
    pred = model.predict(X)
    proba = model.predict_proba(X)[:, 1]
    return {
        "test_accuracy": accuracy_score(y, pred),
        "test_precision": precision_score(y, pred),
        "test_recall": recall_score(y, pred),
        "test_f1": f1_score(y, pred),
        "test_roc_auc": roc_auc_score(y, proba),
    }


def main() -> None:
    MODELS_DIR.mkdir(exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    if data.RAW_PATH.exists():  # always rebuild clean data from raw
        data.save_clean(data.clean(data.load_raw()))
    elif not data.CLEAN_PATH.exists():
        raise SystemExit("No data found. Run scripts/download_data.py first.")
    df = data.load_clean()
    X, y = data.split_xy(df)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=SEED)

    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI",
                                      f"sqlite:///{ROOT / 'mlflow.db'}"))
    mlflow.set_experiment(EXPERIMENT)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    scoring = ["accuracy", "precision", "recall", "roc_auc"]

    results = {}
    for name, (estimator, grid) in CANDIDATES.items():
        pipe = Pipeline([("prep", build_preprocessor()), ("clf", estimator)])
        with mlflow.start_run(run_name=name) as run:
            search = GridSearchCV(pipe, grid, cv=cv, scoring="roc_auc",
                                  n_jobs=-1, refit=True)
            search.fit(X_train, y_train)
            best = search.best_estimator_

            cv_res = cross_validate(best, X_train, y_train, cv=cv,
                                    scoring=scoring)
            cv_metrics = {f"cv_{m}_mean": float(np.mean(cv_res[f"test_{m}"]))
                          for m in scoring}
            cv_metrics.update({f"cv_{m}_std": float(np.std(cv_res[f"test_{m}"]))
                               for m in scoring})
            test_metrics = evaluate(best, X_test, y_test)

            mlflow.log_param("model", name)
            mlflow.log_param("cv_folds", 5)
            mlflow.log_param("test_size", 0.2)
            mlflow.log_param("seed", SEED)
            mlflow.log_params({k: str(v) for k, v in
                               search.best_params_.items()})
            mlflow.log_metrics(cv_metrics)
            mlflow.log_metrics(test_metrics)

            # plots
            fig, ax = plt.subplots(figsize=(5, 4))
            RocCurveDisplay.from_estimator(best, X_test, y_test, ax=ax)
            ax.set_title(f"ROC - {name}")
            roc_path = FIG_DIR / f"roc_{name}.png"
            fig.savefig(roc_path, dpi=150, bbox_inches="tight")
            plt.close(fig)

            fig, ax = plt.subplots(figsize=(4, 4))
            ConfusionMatrixDisplay.from_estimator(best, X_test, y_test, ax=ax)
            ax.set_title(f"Confusion matrix - {name}")
            cm_path = FIG_DIR / f"cm_{name}.png"
            fig.savefig(cm_path, dpi=150, bbox_inches="tight")
            plt.close(fig)

            mlflow.log_artifact(str(roc_path), "plots")
            mlflow.log_artifact(str(cm_path), "plots")
            mlflow.log_artifact(str(data.CLEAN_PATH), "data")
            mlflow.sklearn.log_model(best, "model",
                                     serialization_format="cloudpickle")

            results[name] = {"run_id": run.info.run_id, "model": best,
                             "cv_roc_auc": cv_metrics["cv_roc_auc_mean"],
                             **cv_metrics, **test_metrics,
                             "best_params": search.best_params_}
            print(f"{name}: CV ROC-AUC={cv_metrics['cv_roc_auc_mean']:.3f} "
                  f"test ROC-AUC={test_metrics['test_roc_auc']:.3f} "
                  f"test acc={test_metrics['test_accuracy']:.3f}")

    best_name = max(results, key=lambda n: results[n]["cv_roc_auc"])
    best = results[best_name]["model"]
    joblib.dump(best, MODELS_DIR / "model.joblib")

    summary = {k: {kk: vv for kk, vv in v.items() if kk != "model"}
               for k, v in results.items()}
    summary["best_model"] = best_name
    (MODELS_DIR / "metrics.json").write_text(
        json.dumps(summary, indent=2, default=str))

    with mlflow.start_run(run_name="final_best_model"):
        mlflow.log_param("selected_model", best_name)
        mlflow.log_metrics({k: v for k, v in results[best_name].items()
                            if k.startswith("test_")})
        mlflow.log_artifact(str(MODELS_DIR / "model.joblib"), "joblib")
        mlflow.log_artifact(str(MODELS_DIR / "metrics.json"))
        mlflow.log_artifact(str(ROOT / "requirements.txt"))
    print(f"Best model: {best_name} -> {MODELS_DIR / 'model.joblib'}")


if __name__ == "__main__":
    main()
