# Heart Disease Risk Prediction - MLOps Assignment 01 Report

Name / BITS ID: <fill in>
Repository: https://github.com/<USER>/heart-disease-mlops
Deployed API / access instructions: <port-forward command or URL>

## 1. Problem and dataset
Describe the UCI Heart Disease (Cleveland) dataset: 303 patients, 13 features, target binarised (0 = no disease, 1 = disease). List features and meaning. State the goal.

## 2. Setup and installation
Python version, `pip install -r requirements.txt`, how to run each script (copy from README). Docker and minikube prerequisites.

## 3. EDA
Paste: class balance, histograms, correlation heatmap, boxplots (`reports/figures/`). Write 4-6 observations (missing values in `ca` and `thal`, age/thalach relation to target, class balance).

## 4. Preprocessing and modelling choices
- Median/most-frequent imputation, StandardScaler, OneHotEncoder inside one sklearn Pipeline (no leakage, same transform at inference).
- Models: Logistic Regression, Random Forest. Grid searched hyperparameters with 5-fold stratified CV, scoring ROC-AUC.
- Results table (from `models/metrics.json`): CV and test accuracy, precision, recall, F1, ROC-AUC for both models.
- Justify the selected model.

## 5. Experiment tracking (MLflow)
Screenshots of runs table, run detail (params, metrics, artifacts incl. plots, model), comparison view. Explain what is logged.

## 6. Packaging and reproducibility
joblib model, MLflow model, pinned requirements, preprocessing inside pipeline, fixed seeds.

## 7. CI/CD
Explain workflow stages (lint, test, train, docker build + smoke test, GHCR push, minikube deploy). Screenshots of green run, artifacts, and a deliberately failed run.

## 8. Containerisation and deployment
Architecture diagram (from README mermaid, export as image). Dockerfile explanation. Screenshots: docker build/run/curl, minikube nodes, pods, services, scaling, prediction via service.

## 9. Monitoring and logging
Metrics exposed, Prometheus targets screenshot, Grafana dashboard screenshot, example API request logs.

## 10. Conclusion and limitations
Small dataset, no drift monitoring, no auth, possible improvements (model registry, canary deploys, data validation).
