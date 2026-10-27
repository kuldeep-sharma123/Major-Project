Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "   Starting AI Autonomous Testing Agent Backend   " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

Set-Location -Path "$PSScriptRoot\backend"

# Check if venv exists, if not create it
if (-not (Test-Path "venv")) {
    Write-Host "[+] Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "[+] Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Install dependencies if needed
Write-Host "[+] Checking / Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Install Playwright browser
Write-Host "[+] Installing Playwright Chromium browser..." -ForegroundColor Yellow
playwright install chromium

# Start FastAPI server
Write-Host "==================================================" -ForegroundColor Green
Write-Host " Backend running at: http://localhost:8000       " -ForegroundColor Green
Write-Host " Swagger API docs at: http://localhost:8000/api/docs" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

