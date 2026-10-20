#!/usr/bin/env bash
# Installs the tools this project needs on a Linux lab machine (Ubuntu/Debian).
# Usage:  bash scripts/lab_setup_linux.sh
# Safe to re-run: it only installs what is missing.

have() { command -v "$1" >/dev/null 2>&1; }
SUDO=""
[ "$(id -u)" -ne 0 ] && SUDO="sudo"

echo "== OS =="
head -3 /etc/os-release
echo "user: $(whoami)"

if ! have apt-get; then
  echo "This script supports apt (Ubuntu/Debian) only. Ask the lab admin to install:"
  echo "git, python3 (3.11+), python3-venv, docker, minikube, kubectl"
  exit 1
fi

echo; echo "== basic packages =="
NEED=""
have git      || NEED="$NEED git"
have python3  || NEED="$NEED python3"
have curl     || NEED="$NEED curl"
python3 -m venv --help >/dev/null 2>&1 || NEED="$NEED python3-venv"
have pip3     || NEED="$NEED python3-pip"
if [ -n "$NEED" ]; then
  echo "installing:$NEED"
  $SUDO apt-get update -y && $SUDO apt-get install -y $NEED
else
  echo "git, python3, venv, pip, curl already installed"
fi

echo; echo "== docker =="
if ! have docker; then
  $SUDO apt-get install -y docker.io
fi
$SUDO systemctl start docker 2>/dev/null || $SUDO service docker start 2>/dev/null
if ! docker ps >/dev/null 2>&1; then
  echo "docker needs permission. Adding $(whoami) to the docker group."
  $SUDO usermod -aG docker "$(whoami)"
  echo ">>> LOG OUT AND LOG IN AGAIN (or run: newgrp docker), then re-run this script."
fi

echo; echo "== minikube and kubectl (downloaded to /tmp, NOT into the repo) =="
if ! have minikube; then
  ( cd /tmp && curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64 \
    && $SUDO install minikube-linux-amd64 /usr/local/bin/minikube )
fi
if ! have kubectl; then
  ( cd /tmp && curl -LO "https://dl.k8s.io/release/$(curl -Ls https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" \
    && $SUDO install kubectl /usr/local/bin/kubectl )
fi

echo; echo "== versions =="
python3 --version
python3 -c 'import sys; print("python OK (3.11+)" if sys.version_info >= (3, 11) else "WARNING: python is older than 3.11, pinned libraries may not install")'
git --version
docker --version
docker ps >/dev/null 2>&1 && echo "docker daemon: reachable" || echo "docker daemon: NOT reachable (see messages above)"
minikube version | head -1
kubectl version --client | head -1
echo; echo "Setup finished. Next: bash scripts/lab_demo.sh"
