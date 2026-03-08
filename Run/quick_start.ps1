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

# Step 7: Start ngrok (ถ้ามี) แล้ว Start Server ด้วย URL ngrok
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$ngrokUrl = $null
if (Get-Command ngrok -ErrorAction SilentlyContinue) {
    Write-Host "Starting ngrok (port 8000) first..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "ngrok http 8000"
    Write-Host "Waiting for ngrok tunnel..." -ForegroundColor Gray
    $maxAttempts = 15
    for ($i = 1; $i -le $maxAttempts; $i++) {
        Start-Sleep -Seconds 1
        try {
            $tunnels = Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels" -ErrorAction Stop
            $https = $tunnels.tunnels | Where-Object { $_.public_url -like "https://*" } | Select-Object -First 1
            if ($https -and $https.public_url) {
                $ngrokUrl = $https.public_url.TrimEnd("/")
                Write-Host "OK ngrok URL: $ngrokUrl" -ForegroundColor Green
                break
            }
        } catch {
            if ($i -eq $maxAttempts) {
                Write-Host "ngrok API not ready in time. Server will use config BACKEND_URL." -ForegroundColor Yellow
            }
        }
    }
} else {
    Write-Host "ngrok not found. Server will use config BACKEND_URL. (ติดตั้ง: choco install ngrok)" -ForegroundColor Yellow
}

Write-Host "Starting server in new window..." -ForegroundColor Yellow
$env:PYTHONPATH = "$root\code"
if ($ngrokUrl) {
    $env:BACKEND_URL = $ngrokUrl
    $serverCmd = "Set-Location '$root'; `$env:PYTHONPATH='$root\code'; `$env:BACKEND_URL='$ngrokUrl'; uvicorn main:app --reload --host 0.0.0.0 --port 8000"
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $serverCmd
} else {
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$root'; `$env:PYTHONPATH='$root\code'; uvicorn main:app --reload --host 0.0.0.0 --port 8000"
}
Write-Host "Waiting for server to be ready..." -ForegroundColor Gray
Start-Sleep -Seconds 6

if ($ngrokUrl) {
    Set-Clipboard -Value $ngrokUrl
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "  URL สำหรับแชร์ ( copy ไปวางให้คนอื่นใช้ได้ ): " -ForegroundColor White
    Write-Host "  $ngrokUrl" -ForegroundColor Cyan
    Write-Host "  ( copy ไปที่ Clipboard แล้ว - กด Ctrl+V เพื่อวาง )" -ForegroundColor Gray
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host ""
}

$openUrl = if ($ngrokUrl) { "$ngrokUrl/launch?store_id=1" } else { "http://localhost:8000/launch?store_id=1" }
try {
    Start-Process $openUrl
    Write-Host "Opened browser: Store POS + Signage" -ForegroundColor Green
} catch {
    Write-Host "Open manually: $openUrl" -ForegroundColor Yellow
}
Write-Host "Server (and ngrok if used) running in separate windows. Close those windows to stop." -ForegroundColor Gray
