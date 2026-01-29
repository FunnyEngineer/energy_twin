# Energy Twin Finder - Server Startup Script
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Energy Twin Finder Server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Navigate to project directory
Set-Location $PSScriptRoot

# Activate virtual environment and run server
Write-Host "Starting Flask server..." -ForegroundColor Green
& "$PSScriptRoot\.venv\Scripts\python.exe" "$PSScriptRoot\app.py"
