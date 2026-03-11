$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$venvPython = "$root\backend\venv\Scripts\python.exe"

Write-Host "Forcing dependency re-install..." -ForegroundColor Cyan

if (-not (Test-Path $venvPython)) {
    Write-Error "Virtual environment not found at $venvPython. Please run setup_env.ps1 first."
}

# 1. Upgrade pip
& $venvPython -m pip install --upgrade pip

# 2. Install requirements
& $venvPython -m pip install -r "$root\backend\requirements.txt"

# 3. Check for fastapi
Write-Host "Verifying installation..."
& $venvPython -c "import fastapi; print('FastAPI version:', fastapi.__version__)"

Write-Host "Done! Try running .\start_app.ps1 again." -ForegroundColor Green
