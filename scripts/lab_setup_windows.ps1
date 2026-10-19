# Installs everything needed for this project on a fresh Windows VM.
# Run in an ELEVATED PowerShell (right-click > Run as administrator):
#   Set-ExecutionPolicy -Scope Process Bypass
#   .\scripts\lab_setup_windows.ps1
# If you have not cloned the repo yet, paste the commands below into PowerShell instead.

function Have($cmd) { return [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }

if (-not (Have winget)) {
    Write-Host "winget not found. Install 'App Installer' from the Microsoft Store," -ForegroundColor Yellow
    Write-Host "or install manually: Python 3.12, Git, Docker Desktop, minikube, kubectl, Node.js LTS." -ForegroundColor Yellow
    exit 1
}

$packages = [ordered]@{
    "python"   = "Python.Python.3.12"
    "git"      = "Git.Git"
    "node"     = "OpenJS.NodeJS.LTS"
    "kubectl"  = "Kubernetes.kubectl"
    "minikube" = "Kubernetes.minikube"
    "docker"   = "Docker.DockerDesktop"
}

foreach ($cmd in $packages.Keys) {
    if (Have $cmd) {
        Write-Host "[ok] $cmd already installed"
    } else {
        Write-Host "[install] $cmd ($($packages[$cmd]))" -ForegroundColor Cyan
        winget install -e --id $packages[$cmd] --accept-source-agreements --accept-package-agreements
    }
}

Write-Host ""
Write-Host "Done. NEXT STEPS:" -ForegroundColor Green
Write-Host " 1. CLOSE this window and open a NEW PowerShell (so PATH updates)."
Write-Host " 2. Start Docker Desktop from the Start menu, accept the license, wait for 'Engine running'."
Write-Host "    If it asks to enable WSL 2 / restart, do so, then start Docker Desktop again."
Write-Host " 3. Verify:  python --version; git --version; docker version; minikube version; kubectl version --client"
Write-Host "    'docker version' must show BOTH Client and Server sections."
Write-Host " 4. Copilot CLI (optional): in Git Bash run  curl -fsSL https://gh.io/copilot-install | bash"
Write-Host "    or in PowerShell:  npm install -g @github/copilot   then run:  copilot"
