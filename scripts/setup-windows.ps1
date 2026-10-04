$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
if (-not (Test-Path ".venv")) {
    py -3 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw "Python environment creation failed." }
}
& .\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed." }
if (-not (Test-Path ".env")) { Copy-Item .env.example .env }
Write-Output "Dependencies ready. Fill in .env using GMAIL_SETUP.md before running the app. Then run .\.venv\Scripts\python.exe run.py, then worker.py in a second terminal."
