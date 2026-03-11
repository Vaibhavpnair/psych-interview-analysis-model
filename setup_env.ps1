$ErrorActionPreference = "Stop"

Write-Host "Setting up Psychiatric Interview System Environment..." -ForegroundColor Cyan

# 1. Backend Setup
$backendPath = Join-Path $PSScriptRoot "backend"
Set-Location $backendPath

Write-Host "Checking Backend Environment..." -ForegroundColor Yellow

# Create venv if not exists
if (-not (Test-Path "venv")) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Green
    python -m venv venv
}

# Activate venv
Write-Host "Activating virtual environment..."
& ".\venv\Scripts\Activate.ps1"

# Install dependencies
Write-Host "Installing Python dependencies (this may take a few minutes)..." -ForegroundColor Green
pip install --upgrade pip
pip install -r requirements.txt

# Download Spacy model
Write-Host "Downloading spaCy model (en_core_web_sm)..." -ForegroundColor Green
python -m spacy download en_core_web_sm

# 2. Frontend Setup
$frontendPath = Join-Path $PSScriptRoot "frontend"
Set-Location $frontendPath

Write-Host "Checking Frontend Environment..." -ForegroundColor Yellow
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing Node modules..." -ForegroundColor Green
    npm install
}

Write-Host "Setup Complete! You can now run .\start_app.ps1" -ForegroundColor Cyan
