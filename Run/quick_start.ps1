# Quick Start Script for Windows PowerShell
# Market_Place_System - โครงสร้าง: README (root), code/, Run/, Deploy/

$root = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $root

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Market_Place_System - Quick Start" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check Python
Write-Host "Step 1: Checking Python..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "OK Python found: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "Python not found! Please install Python 3.12+" -ForegroundColor Red
    exit 1
}

# Step 2: Install Dependencies
Write-Host ""
Write-Host "Step 2: Installing dependencies (code/)..." -ForegroundColor Yellow
python -m pip install --upgrade pip
python -m pip install -r code/requirements.txt
if ($LASTEXITCODE -eq 0) {
    Write-Host "OK Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "Some dependencies may have conflicts" -ForegroundColor Yellow
}

# Step 3: Check Setup (Run scripts ต้องเห็น code/)
Write-Host ""
Write-Host "Step 3: Checking setup..." -ForegroundColor Yellow
$env:PYTHONPATH = "$root\code"
python Run/check_setup.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "Setup check found issues" -ForegroundColor Yellow
}

# Step 4: Create Database
Write-Host ""
Write-Host "Step 4: Creating database..." -ForegroundColor Yellow
python Run/create_database.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "Database creation had issues" -ForegroundColor Yellow
}

# Step 5: Initialize Database
Write-Host ""
Write-Host "Step 5: Initializing database..." -ForegroundColor Yellow
python Run/init_db.py
if ($LASTEXITCODE -eq 0) {
    Write-Host "OK Database initialized" -ForegroundColor Green
} else {
    Write-Host "Database initialization failed" -ForegroundColor Red
    exit 1
}

# Step 6: Create Sample Data
Write-Host ""
Write-Host "Step 6: Creating sample data..." -ForegroundColor Yellow
python Run/create_sample_data.py
if ($LASTEXITCODE -eq 0) {
    Write-Host "OK Sample data created" -ForegroundColor Green
}

# Step 7: Start Server
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To start the server manually (from project root):" -ForegroundColor Yellow
Write-Host "  `$env:PYTHONPATH='code'; uvicorn main:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor White
Write-Host ""
Write-Host "Then open:" -ForegroundColor Yellow
Write-Host "  http://localhost:8000/docs - API Documentation" -ForegroundColor White
Write-Host "  http://localhost:8000/launch?store_id=1 - Store POS + Signage" -ForegroundColor White
Write-Host ""

Write-Host "Starting server in new window..." -ForegroundColor Yellow
$env:PYTHONPATH = "$root\code"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$root'; `$env:PYTHONPATH='$root\code'; uvicorn main:app --reload --host 0.0.0.0 --port 8000"
Write-Host "Waiting for server to be ready..." -ForegroundColor Gray
Start-Sleep -Seconds 6
try {
    Start-Process "http://localhost:8000/launch?store_id=1"
    Write-Host "Opened browser: Store POS + Signage" -ForegroundColor Green
} catch {
    Write-Host "Open manually: http://localhost:8000/launch?store_id=1" -ForegroundColor Yellow
}
Write-Host "Server is running in the other window. Close that window to stop server." -ForegroundColor Gray
