Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Starting AI Autonomous Testing Agent Frontend   " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

Set-Location -Path "$PSScriptRoot\frontend"

# Check if node_modules exists
if (-not (Test-Path "node_modules")) {
    Write-Host "[+] Installing Node.js packages..." -ForegroundColor Yellow
    npm install
}

Write-Host "==================================================" -ForegroundColor Green
Write-Host " Frontend running at: http://localhost:3000      " -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green

npm run dev

