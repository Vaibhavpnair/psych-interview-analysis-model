# Launch Backend and Frontend in separate windows

$root = $PSScriptRoot

Write-Host "Starting Psychiatric Decision Support System..." -ForegroundColor Cyan

# Check if setup has been run
if (-not (Test-Path "$root\backend\venv")) {
    Write-Warning "Virtual environment not found. Please run .\setup_env.ps1 first."
    exit
}

# 1. Start Backend
Write-Host "Launching Backend (FastAPI)..." -ForegroundColor Green
# We pass the full command to activate venv and run uvicorn
$backendCommand = "cd '$root\backend'; .\venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --port 8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCommand

# 2. Start Frontend
Write-Host "Launching Frontend (React)..." -ForegroundColor Green
$frontendCommand = "cd '$root\frontend'; npm run dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCommand

Write-Host "System Launching!" 
Write-Host "Backend will be at: http://localhost:8000/docs"
Write-Host "Frontend will be at: http://localhost:5173"
