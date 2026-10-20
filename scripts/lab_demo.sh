#!/usr/bin/env bash
# Runs the whole project in stages, pausing after each so you can take a screenshot.
#
#   bash scripts/lab_demo.sh          run all stages in order
#   bash scripts/lab_demo.sh 5        run only stage 5
#   bash scripts/lab_demo.sh 7 8      run stages 7 and 8
#   bash scripts/lab_demo.sh cleanup  stop background processes, delete the cluster
#
# Stages: 1 tools  2 train+MLflow  3 tests  4 API local  5 Docker
#         6 GHCR   7 Kubernetes    8 Prometheus+Grafana
#
# Run it from the repo folder in a terminal with a big font, screen recording on.

cd "$(dirname "$0")/.." || exit 1
GH_USER="jpmayandi"
IMAGE="heart-disease-api:latest"
PIDS=/tmp/heart_demo_pids
touch "$PIDS"

banner() { echo; echo "=========================================================="; echo "  $*"; echo "=========================================================="; }
shot()   { echo; echo "  >>> SCREENSHOT: $1"; read -r -p "  >>> Take it now, then press Enter to continue... " _; }
run()    { echo; echo "\$ $*"; eval "$*"; }
bg()     { # bg "command" -> run in background, remember pid
  echo; echo "\$ $*   (background)"; eval "$* &"; echo $! >> "$PIDS"; }
use_venv() { [ -f .venv/bin/activate ] && . .venv/bin/activate; }

stop_bg() {
  while read -r p; do [ -n "$p" ] && kill "$p" 2>/dev/null; done < "$PIDS"
  : > "$PIDS"
  pkill -f "minikube tunnel" 2>/dev/null
}

s1() {
  banner "1. Tools and repository"
  run "pwd && ls -a"
  run "python3 --version"
  run "git --version"
  run "docker version --format 'client {{.Client.Version}}  server {{.Server.Version}}'"
  run "minikube version | head -1"
  run "kubectl version --client | head -1"
  shot "01_clone_and_tools.png (clone, ls and versions; docker must show a server version)"
}

s2() {
  banner "2. Data, EDA, training, MLflow"
  [ -d .venv ] || run "python3 -m venv .venv"
  use_venv
  run "pip install -r requirements.txt 2>&1 | tail -5"
  shot "02_pip_install.png"
  run "python scripts/download_data.py"
  run "python -m src.eda 2>&1 | tail -15"
  shot "03_download_eda.png"
  run "python -m src.train 2>&1 | grep -v -i warn"
  run "cat models/metrics.json | head -40"
  shot "04_training_output.png (both models' scores and Best model line)"
  echo "  Open the folder reports/figures and screenshot class_balance.png + correlation_heatmap.png (05_eda_figures.png)"
  shot "05_eda_figures.png"
  bg "nohup mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5000 > /tmp/mlflow.log 2>&1"
  sleep 6
  echo "  Open http://localhost:5000 in the browser:"
  echo "   - experiment heart-disease-classification, runs table          -> 06_mlflow_runs.png"
  echo "   - tick both model runs, click Compare                          -> 07_mlflow_compare.png"
  echo "   - open one run (parameters, metrics, artifacts)                -> 08_mlflow_run_detail.png"
  shot "06, 07 and 08 MLflow screenshots"
  stop_bg
}

s3() {
  banner "3. Unit tests and lint"
  use_venv
  run "pytest -v 2>&1 | tail -25"
  run "flake8 . && echo 'flake8: no problems'"
  shot "09_tests_lint.png"
}

s4() {
  banner "4. API running locally"
  use_venv
  bg "nohup uvicorn api.app:app --port 8000 > /tmp/uvicorn.log 2>&1"
  sleep 6
  run "curl -s localhost:8000/health; echo"
  run "curl -s -X POST localhost:8000/predict -H 'Content-Type: application/json' -d @sample_request.json; echo"
  run "curl -s localhost:8000/metrics | grep -E '^(api_|predictions_|model_loaded)'"
  shot "10_api_local_curl.png"
  echo "  Open http://localhost:8000/docs in the browser -> 11_api_swagger.png"
  shot "11_api_swagger.png"
  stop_bg
}

s5() {
  banner "5. Docker build, run, test"
  run "docker build -t $IMAGE ."
  shot "12_docker_build.png"
  run "docker rm -f heart-api >/dev/null 2>&1; docker run -d --name heart-api -p 8001:8000 $IMAGE"
  sleep 5
  run "docker ps"
  run "curl -s localhost:8001/health; echo"
  run "curl -s -X POST localhost:8001/predict -H 'Content-Type: application/json' -d @sample_request.json; echo"
  run "docker logs heart-api | head"
  shot "13_docker_run_test.png (docker ps, both curls, 'Model loaded from /app/models/model.joblib')"
  run "docker stop heart-api && docker rm heart-api"
}

s6() {
  banner "6. Image from GitHub Container Registry"
  run "docker pull ghcr.io/$GH_USER/heart-disease-api:latest || echo 'pull failed: package private or not pushed yet (make it public on GitHub)'"
  run "docker images | grep heart"
  shot "14_ghcr_pull.png"
  echo "  In the browser: GitHub profile > Packages > heart-disease-api -> 15_ghcr_package.png"
  shot "15_ghcr_package.png"
}

s7() {
  banner "7. Minikube, deploy, scale, LoadBalancer, logs"
  docker image inspect "$IMAGE" >/dev/null 2>&1 || run "docker build -t $IMAGE ."
  # --cni=bridge avoids downloading the network plugin (fixes NotReady nodes when registries are blocked)
  run "minikube start --driver=docker --cpus=2 --memory=2048 --cni=bridge"
  run "kubectl wait --for=condition=Ready node/minikube --timeout=120s"
  run "kubectl get nodes"
  shot "16_minikube_start_nodes.png"
  run "minikube image load $IMAGE"
  run "minikube image ls | grep heart"
  shot "17_image_loaded.png"
  run "kubectl apply -f k8s/deployment.yaml -f k8s/service.yaml"
  run "kubectl rollout status deployment/heart-api --timeout=180s"
  run "kubectl get deploy,svc,pods"
  shot "18_pods_running.png"
  run "kubectl scale deployment heart-api --replicas=4"
  run "kubectl rollout status deployment/heart-api --timeout=120s"
  run "kubectl get pods"
  shot "19_scale_up_4.png"
  run "kubectl scale deployment heart-api --replicas=2"
  sleep 15
  run "kubectl get pods"
  shot "20_scale_down_2.png"
  pkill -f "minikube tunnel" 2>/dev/null
  bg "nohup minikube tunnel > /tmp/tunnel.log 2>&1"
  echo "  waiting for the LoadBalancer address..."
  EXT=""
  for _ in $(seq 1 20); do
    EXT=$(kubectl get svc heart-api -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null)
    [ -n "$EXT" ] && break
    sleep 3
  done
  run "kubectl get svc heart-api"
  shot "21_loadbalancer_ip.png"
  if [ -z "$EXT" ]; then
    echo "  No external IP (tunnel problem). Falling back to port-forward on localhost:8080."
    bg "nohup kubectl port-forward svc/heart-api 8080:80 > /tmp/pf-api.log 2>&1"
    sleep 4
    BASE="http://localhost:8080"
  else
    BASE="http://$EXT"
  fi
  run "curl -s $BASE/health; echo"
  run "curl -s -X POST $BASE/predict -H 'Content-Type: application/json' -d @sample_request.json; echo"
  shot "22_k8s_prediction.png"
  run "for i in 1 2 3 4 5; do curl -s $BASE/health >/dev/null; done"
  run "kubectl logs -l app=heart-api --tail=10 --prefix"
  shot "23_k8s_logs.png"
  echo "  (leave this running: the tunnel/port-forward keeps the API reachable. Stage 8 uses it.)"
}

s8() {
  banner "8. Prometheus and Grafana"
  use_venv
  run "docker pull prom/prometheus:latest"
  run "docker pull grafana/grafana:latest"
  run "minikube image load prom/prometheus:latest"
  run "minikube image load grafana/grafana:latest"
  run "kubectl delete configmap grafana-dashboards --ignore-not-found"
  run "kubectl create configmap grafana-dashboards --from-file=heart-api.json=k8s/grafana-dashboard.json"
  run "kubectl apply -f k8s/prometheus.yaml -f k8s/grafana.yaml"
  run "kubectl rollout status deployment/prometheus --timeout=180s"
  run "kubectl rollout status deployment/grafana --timeout=180s"
  run "kubectl get pods"
  shot "24_monitoring_pods.png"
  bg "nohup kubectl port-forward svc/prometheus 9090:9090 > /tmp/pf-prom.log 2>&1"
  bg "nohup kubectl port-forward svc/grafana 3000:3000 > /tmp/pf-graf.log 2>&1"
  bg "nohup kubectl port-forward svc/heart-api 8080:80 > /tmp/pf-api2.log 2>&1"
  sleep 5
  run "python scripts/send_traffic.py http://localhost:8080 200"
  echo "  Browser steps:"
  echo "   http://localhost:9090/targets  (heart-api UP)                -> 25_prometheus_targets.png"
  echo "   http://localhost:9090  query: sum(api_requests_total)       -> 26_prometheus_query.png"
  echo "   http://localhost:3000  login admin / admin,"
  echo "      Dashboards > Heart Disease API, range Last 15 minutes    -> 27_grafana_dashboard.png"
  echo "      then build your own panel (Dashboards > New > Add visualization >"
  echo "      Prometheus > sum by (endpoint) (rate(api_requests_total[1m])) > Save) -> 28_grafana_own_panel.png"
  echo "   If panels are empty, run again: python scripts/send_traffic.py http://localhost:8080 200"
  shot "25 to 28 Prometheus and Grafana screenshots"
}

cleanup() {
  banner "Cleanup"
  stop_bg
  docker rm -f heart-api >/dev/null 2>&1
  run "minikube delete"
}

if [ "$1" = "cleanup" ]; then cleanup; exit 0; fi

use_venv
if [ $# -eq 0 ]; then set -- 1 2 3 4 5 6 7 8; fi
for st in "$@"; do
  "s$st" || echo "stage $st reported a problem; read the messages above"
done
banner "Done. GitHub screenshots (29 to 32) are taken in the browser. When finished: bash scripts/lab_demo.sh cleanup"
