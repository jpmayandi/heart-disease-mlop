# RUNBOOK - Step by step (4-hour plan)

Replace `<USER>` with your GitHub username (lowercase) everywhere.

## Time plan

| Time | Step |
|---|---|
| 0:00-0:20 | Part 0: GitHub account, repo, Codespace, upload code |
| 0:20-0:50 | Part 1: data, EDA, training, MLflow (commit stage 1-3) |
| 0:50-1:10 | Part 2: tests + API (commit stage 4) |
| 1:10-1:40 | Part 3: Docker build/run + GHCR push (commit stage 5) |
| 1:40-2:20 | Part 4: Minikube, kubectl, scale (commit stage 6) |
| 2:20-2:50 | Part 5: Prometheus + Grafana (commit stage 7) |
| 2:50-3:10 | Part 6: GitHub Actions run + screenshots |
| 3:10-3:40 | Part 7: lab run + screen recording |
| 3:40-4:00 | Part 8: report (use screenshots already taken) |

Take screenshots as you go. Save them in `screenshots/` with names like `01_eda.png`, `02_mlflow_runs.png`, `03_docker_run.png`, `04_pods.png`, `05_grafana.png`, `06_actions.png`.

---

## Part 0 - GitHub, repo, Codespace

1. Create an account at https://github.com/signup (use your BITS email so Copilot access applies).
2. New repository: name `heart-disease-mlops`, Public, no README (the project has one). Public makes the GHCR image easy to pull later.
3. Open the repo, click **Code > Codespaces > Create codespace on main**.
4. Get the project into the Codespace: drag the unzipped project folder contents into the Codespace file explorer (or upload the zip and run `unzip heart-disease-mlops.zip` then `mv heart-disease-mlops/* heart-disease-mlops/.[!.]* . ` and delete the empty folder).
5. Check `ls -a` shows `src api k8s tests Dockerfile .github`.

Stage 0 commit:

```bash
git add -A
git commit -m "stage 0: project scaffold"
git push origin main
```

> The first push will start the CI workflow. It may fail until the model exists. That is fine; it will pass after Stage 1/2.

## Part 1 - Data, EDA, training, MLflow

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/download_data.py
python -m src.eda
python -m src.train
```

If `download_data.py` fails (network), download `processed.cleveland.data` from the UCI repository page linked in your assignment manually and save it as `data/raw/heart_raw.csv` with header `age,sex,cp,trestbps,chol,fbs,restecg,thalach,exang,oldpeak,slope,ca,thal,target`.

View MLflow:

```bash
mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5000
```

Codespaces shows a popup to open port 5000 (or use the **Ports** tab). Screenshot the runs table, one run's params/metrics/artifacts, and the comparison view (select both runs > Compare).

Commit:

```bash
git add -A && git commit -m "stage 1: data, EDA, training with MLflow" && git push
```

Remember the dataset: `data/processed/heart_clean.csv` and `models/model.joblib` are committed (the `.gitignore` allows them) so Docker and CI work.

## Part 2 - Tests and API

```bash
pytest -v
flake8 .
uvicorn api.app:app --port 8000
```

In a second terminal:

```bash
curl localhost:8000/health
curl -X POST localhost:8000/predict -H 'Content-Type: application/json' \
  -d '{"age":63,"sex":1,"cp":1,"trestbps":145,"chol":233,"fbs":1,"restecg":2,"thalach":150,"exang":0,"oldpeak":2.3,"slope":3,"ca":0,"thal":6}'
# (or, on any OS: curl -X POST localhost:8000/predict -H "Content-Type: application/json" -d @sample_request.json)
curl localhost:8000/metrics | head -30
```

Also open `/docs` (Swagger UI) and screenshot it.

```bash
git add -A && git commit -m "stage 2: unit tests and prediction API" && git push
```

## Part 3 - Docker and GHCR

```bash
docker build -t heart-disease-api:latest .
docker run -d --name heart-api -p 8000:8000 heart-disease-api:latest
curl localhost:8000/health
curl -X POST localhost:8000/predict -H 'Content-Type: application/json' \
  -d '{"age":63,"sex":1,"cp":1,"trestbps":145,"chol":233,"fbs":1,"restecg":2,"thalach":150,"exang":0,"oldpeak":2.3,"slope":3,"ca":0,"thal":6}'
docker logs heart-api | tail
docker stop heart-api && docker rm heart-api
```

Screenshot the build, the run, and the curl result (this is the required "Docker build/test proof").

Push to GHCR. Create a Personal Access Token (classic) at GitHub > Settings > Developer settings > Tokens (classic) with scope `write:packages` (and `read:packages`):

```bash
echo <TOKEN> | docker login ghcr.io -u <USER> --password-stdin
docker tag heart-disease-api:latest ghcr.io/<USER>/heart-disease-api:latest
docker push ghcr.io/<USER>/heart-disease-api:latest
```

Then on GitHub: your profile > Packages > heart-disease-api > Package settings > Change visibility > Public. Link it to the repo if offered.

```bash
git add -A && git commit -m "stage 3: Dockerfile and GHCR image" && git push
```

## Part 4 - Minikube, kubectl, scaling

Install (Codespaces / lab, if missing):

```bash
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube
kubectl version --client || (curl -LO "https://dl.k8s.io/release/$(curl -Ls https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && sudo install kubectl /usr/local/bin/kubectl)
```

Start the cluster and load the image into the node:

```bash
minikube start --driver=docker
kubectl get nodes

# Option A: load the local image into the node
minikube image load heart-disease-api:latest
# Option B: pull from GHCR (public) and use that name in k8s/deployment.yaml
#   minikube ssh -- docker pull ghcr.io/<USER>/heart-disease-api:latest
minikube image ls | grep heart
```

Deploy, run, scale:

```bash
kubectl apply -f k8s/deployment.yaml -f k8s/service.yaml
kubectl get pods -w            # Ctrl+C when 2/2 Running
kubectl get deploy,svc
kubectl scale deployment heart-api --replicas=4
kubectl get pods
kubectl scale deployment heart-api --replicas=2
kubectl logs deploy/heart-api --tail=20
kubectl describe pod -l app=heart-api | head -40
```

Reach the service:

```bash
kubectl port-forward svc/heart-api 8080:80 &
curl localhost:8080/health
curl -X POST localhost:8080/predict -H 'Content-Type: application/json' \
  -d '{"age":63,"sex":1,"cp":1,"trestbps":145,"chol":233,"fbs":1,"restecg":2,"thalach":150,"exang":0,"oldpeak":2.3,"slope":3,"ca":0,"thal":6}'
```

(`minikube service heart-api --url` also works on a machine with a browser. For the "LoadBalancer" wording of the assignment: change `type: NodePort` to `LoadBalancer` in `k8s/service.yaml` and run `minikube tunnel` in another terminal.)

To use the GHCR image instead of the local one, set `image: ghcr.io/<USER>/heart-disease-api:latest` in `k8s/deployment.yaml`.

Screenshot: `kubectl get nodes`, `kubectl get pods,svc`, the scale output, and the curl prediction.

```bash
git add -A && git commit -m "stage 4: kubernetes deployment" && git push
```

## Part 5 - Prometheus and Grafana

Pull images on the host, load them into minikube, then deploy:

```bash
docker pull prom/prometheus:latest
docker pull grafana/grafana:latest
minikube image load prom/prometheus:latest
minikube image load grafana/grafana:latest

kubectl create configmap grafana-dashboards --from-file=heart-api.json=k8s/grafana-dashboard.json
kubectl apply -f k8s/prometheus.yaml -f k8s/grafana.yaml
kubectl get pods
```

The API already exposes `/metrics` (request counts, latency histogram, prediction counts, confidence, model loaded) - this is the "metrics API".

Open the UIs:

```bash
kubectl port-forward svc/prometheus 9090:9090 &
kubectl port-forward svc/grafana 3000:3000 &
```

In Codespaces use the **Ports** tab to open 9090 and 3000.

1. Prometheus: Status > Targets, `heart-api` should be UP. Try query `sum(api_requests_total)`.
2. Generate traffic:

```bash
python scripts/send_traffic.py http://localhost:8080 100
```

3. Grafana: login `admin` / `admin`. The datasource and the **Heart Disease API** dashboard are pre-provisioned (Dashboards menu). To show you built a dashboard yourself, also create a new one: Dashboards > New > Add visualization > Prometheus > query `sum by (endpoint) (rate(api_requests_total[1m]))`, save.

Screenshot Prometheus targets and the Grafana dashboard with live data.

```bash
git add -A && git commit -m "stage 5: Prometheus and Grafana monitoring" && git push
```

## Part 6 - GitHub Actions

The pipeline in `.github/workflows/ci.yml` runs: lint > tests > train (uploads model, MLflow DB, figures as artifacts) > Docker build + container smoke test + push to GHCR (main only) > minikube deploy, scale and endpoint verification.

1. Repo > **Actions** tab, open the latest run. Screenshot the job graph (all green) and the artifacts section.
2. Show the pipeline fails on errors (assignment requirement): create a branch, break a test (e.g., change an assertion in `tests/test_data.py`), push, screenshot the red run, then revert.
3. If GHCR push fails with permission denied: repo > Settings > Actions > General > Workflow permissions > Read and write.

## Part 7 - Lab run and screen recording

In the lab terminal / VS Code:

```bash
curl -fsSL https://gh.io/copilot-install | bash
copilot            # follow the login prompt with your BITS GitHub account
```

Use Copilot to fix any dependency issue (describe the error in plain text).

```bash
git clone https://github.com/<USER>/heart-disease-mlops.git
cd heart-disease-mlops
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/download_data.py && python -m src.eda && python -m src.train
pytest -v
docker build -t heart-disease-api:latest .
minikube start --driver=docker
minikube image load heart-disease-api:latest
kubectl apply -f k8s/deployment.yaml -f k8s/service.yaml
# monitoring (Part 5 commands)
```

Record with **Clipchamp** (Teams plugin from BITS): screen + mic, 5-8 minutes. Suggested script:

1. Show the repo and folder structure (30 s).
2. Run EDA/training, show the MLflow UI (1 min).
3. `pytest`, `docker build`, `docker run`, curl (1.5 min).
4. `minikube start`, load image, `kubectl apply`, `kubectl get pods`, scale (1.5 min).
5. Prometheus targets, Grafana dashboard with traffic (1.5 min).
6. GitHub Actions page, all green (30 s).

Do a dry run first. Pre-pull images (`docker pull ...`) before recording so you do not wait on downloads on camera.

### Part 7b - If the lab is a Windows VM (read this first)

**Nothing installed? Start with `docs/LAB_SETUP_WINDOWS.md` and `scripts/lab_setup_windows.ps1`** (installs Python, Git, Node, kubectl, minikube, Docker Desktop, and explains what to do if the VM cannot run Docker).

Parts 0-6 (Codespaces, Linux) are unchanged. Only the lab differs. First check what the lab has. In PowerShell run:

```powershell
python --version; git --version; docker version; minikube version; kubectl version --client
```

Install what is missing: `winget install Python.Python.3.12 Git.Git Docker.DockerDesktop Kubernetes.minikube Kubernetes.kubectl` (or ask the lab for the installers). Docker Desktop must be running (WSL2 backend) before `minikube start --driver=docker`. If `docker version` shows no Server, or Docker Desktop cannot start inside the VM (nested virtualisation off), ask the lab admin; without Docker you cannot do the Docker/minikube parts there and should use your Codespace for those recordings.

Use **Git Bash** or **WSL** if available: then every command in this runbook works as written, except `source .venv/bin/activate` becomes `source .venv/Scripts/activate` in Git Bash. The Copilot installer (`curl -fsSL https://gh.io/copilot-install | bash`) also needs Git Bash/WSL. In plain PowerShell, install it with npm instead (needs Node.js): `npm install -g @github/copilot`, then run `copilot`.

If you use plain **PowerShell**, translate like this:

| Linux (runbook) | PowerShell |
|---|---|
| `source .venv/bin/activate` | `.venv\Scripts\Activate.ps1` (if blocked: `Set-ExecutionPolicy -Scope Process Bypass`) |
| `python3` | `python` |
| `curl ...` | `curl.exe ...` (plain `curl` is a different PowerShell command) |
| multi-line `\` | one line, or end lines with a backtick |
| JSON in `-d '...'` | `curl.exe -X POST localhost:8000/predict -H "Content-Type: application/json" -d "@sample_request.json"` |
| `kubectl port-forward ... &` | open a second PowerShell window per port-forward |
| `for i in $(seq ...)` traffic loop | `python scripts/send_traffic.py http://localhost:8080 100` |
| `sudo install minikube...` | `winget install Kubernetes.minikube` |
| `grep` / `head` / `tail` | `Select-String` / `Select-Object -First 20` / `Select-Object -Last 20` |

Lab run order in PowerShell:

```powershell
git clone https://github.com/<USER>/heart-disease-mlops.git
cd heart-disease-mlops
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/download_data.py
python -m src.eda
python -m src.train
pytest -v
docker build -t heart-disease-api:latest .
docker run -d --name heart-api -p 8000:8000 heart-disease-api:latest
curl.exe -X POST localhost:8000/predict -H "Content-Type: application/json" -d "@sample_request.json"
docker stop heart-api; docker rm heart-api
minikube start --driver=docker
minikube image load heart-disease-api:latest
kubectl apply -f k8s/deployment.yaml -f k8s/service.yaml
kubectl get pods
```

Notes: the Docker images are Linux containers, which Docker Desktop runs fine on Windows. Browser URLs such as `http://localhost:5000` (MLflow), `:9090`, `:3000` work from the VM browser. The lab may block downloads from some sites; if `download_data.py` fails, the committed `data/processed/heart_clean.csv` lets `python -m src.train` still run (skip the download and EDA steps).

## Part 8 - Report (about 10 pages)

Use `docs/REPORT_TEMPLATE.md` as the skeleton; paste in your real metrics from `models/metrics.json`, your screenshots, and your repo link. Export to PDF/DOCX.

## Troubleshooting

| Problem | Fix |
|---|---|
| `ImagePullBackOff` | `minikube image load` the image, keep `imagePullPolicy: IfNotPresent`, check image name matches |
| Pod `CrashLoopBackOff` | `kubectl logs <pod>`; usually missing `models/model.joblib` in the image (is it committed?) |
| Pickle/sklearn version error | Use the pinned `requirements.txt` in both training and Docker |
| Minikube won't start in Codespaces | Use 4+ core machine type; `minikube delete && minikube start --driver=docker` |
| GHCR `denied` | Token needs `write:packages`; image name must be lowercase |
| Grafana shows no data | Prometheus Targets page must show UP; send traffic; set range to last 15 min |
| MLflow `mlruns` store error | Use the sqlite URI exactly as in the commands above |
