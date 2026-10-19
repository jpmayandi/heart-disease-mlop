# Lab setup on a fresh Windows VM

Assume nothing is installed. Do this once, before recording. Needs admin rights and internet access. Budget 20-30 minutes (Docker Desktop is the slow part).

## 1. Check what you are allowed to do (2 min)

Open PowerShell as administrator (Start > type "PowerShell" > right-click > Run as administrator).

```powershell
whoami /groups | Select-String "Administrators"
winget --version
```

If you are not admin or `winget` is missing, ask the lab admin to install the tools in step 2 or enable winget ("App Installer").

## 2. Install everything (10-20 min)

If the repo is not cloned yet, install Git first, then clone:

```powershell
winget install -e --id Git.Git --accept-source-agreements --accept-package-agreements
# close and reopen PowerShell, then:
git clone https://github.com/<USER>/heart-disease-mlops.git
cd heart-disease-mlops
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\lab_setup_windows.ps1
```

This installs Python 3.12, Git, Node.js, kubectl, minikube and Docker Desktop through winget. If one package fails, find the right id with `winget search <name>` and install it by hand, or use the vendor installer.

Then **close PowerShell, open a new one**, start **Docker Desktop**, and wait until it says the engine is running (restart Windows if it asks).

## 3. Verify (1 min)

```powershell
python --version
git --version
docker version
minikube version
kubectl version --client
```

`docker version` must print a **Server** section. Without it, Docker is not running.

## 4. If Docker Desktop will not start (common in VMs)

Docker Desktop and minikube both need virtualization, so the Windows VM must allow nested virtualization. Typical error text: "Virtualization support not detected", "WSL 2 installation is incomplete", or Hyper-V cannot start.

What to do, in order:
1. Reboot once, run `wsl --update`, start Docker Desktop again.
2. Ask the lab admin whether nested virtualization is enabled for your VM. This is a setting on the host (Linux/KVM side); you cannot fix it from inside Windows.
3. If it cannot be enabled: do the Python parts in the lab (EDA, training, MLflow, pytest, the API with `uvicorn`), and record the **Docker, minikube, Prometheus and Grafana** parts in your **GitHub Codespace**, which already has Docker. Say so in the report and the video. Tell your instructor early; do not hide it.

## 5. Run the project (Windows, PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/download_data.py
python -m src.eda
python -m src.train
pytest -v
mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5000
```

Then continue with Part 3 onward of `docs/RUNBOOK.md`, using the PowerShell translations in Part 7b.

The lab firewall can block some sites. If `download_data.py` fails, download the dataset in your browser from the UCI link in the assignment, or run training from the committed `data/processed/heart_clean.csv` (skip the download and EDA steps).

## 6. Copilot CLI and recording

- Copilot: in **Git Bash** run `curl -fsSL https://gh.io/copilot-install | bash`, then type `copilot` and log in with your BITS GitHub account. In PowerShell use `npm install -g @github/copilot` instead.
- Recording: Clipchamp from the Teams plugin. Pre-pull images and warm up Docker/minikube before you hit record.
