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

# Step 2b: ติดตั้ง Stripe CLI (ถ้ามี Scoop) — ใช้รับ webhook ทดสอบโดยไม่โดน ngrok 403
Write-Host ""
Write-Host "Step 2b: Stripe CLI (optional, for webhook)..." -ForegroundColor Yellow
if (Get-Command scoop -ErrorAction SilentlyContinue) {
    $stripeBucket = scoop bucket list 2>$null | Select-String "stripe"
    if (-not $stripeBucket) {
        scoop bucket add stripe https://github.com/stripe/scoop-stripe-cli.git 2>$null
    }
    if (-not (Get-Command stripe -ErrorAction SilentlyContinue)) {
        scoop install stripe 2>$null
        if (Get-Command stripe -ErrorAction SilentlyContinue) {
            Write-Host "OK Stripe CLI installed (ทางเลือก: stripe listen; ระบบใช้ Stripe API/ngrok เป็นหลัก)" -ForegroundColor Green
        } else {
            Write-Host "Stripe CLI install skipped or failed. ติดตั้งมือ: scoop install stripe" -ForegroundColor Gray
        }
    } else {
        Write-Host "OK Stripe CLI already installed" -ForegroundColor Green
    }
} else {
    Write-Host "Scoop not found. ติดตั้ง Stripe CLI เอง: ดู code/docs/STRIPE_NGROK.md" -ForegroundColor Gray
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

# Step 6b: Seed stores + menus + users สำหรับ Store POS (สร้าง/ผูกเมนูและ user ถ้ายังไม่มี)
Write-Host ""
Write-Host "Step 6b: Seeding stores, menus, and Store POS users..." -ForegroundColor Yellow
$env:PYTHONPATH = "$root\code"
python Run/seed_stores_menus_users.py
if ($LASTEXITCODE -eq 0) {
    Write-Host "OK Stores, menus, and POS users ready" -ForegroundColor Green
}

# Step 6c: Seed สมาชิก (Member) ตัวอย่าง สำหรับ /member ลงทะเบียน-ล็อกอิน
Write-Host ""
Write-Host "Step 6c: Seeding sample members..." -ForegroundColor Yellow
python Run/seed_members.py
if ($LASTEXITCODE -eq 0) {
    Write-Host "OK Sample members ready (member1/member123, demo/demo1234)" -ForegroundColor Green
}

# Step 7: เครียร์เฉพาะ port 8000 (Uvicorn) — ไม่ฆ่า ngrok (4040) เพื่อไม่เกินโควต้า 1 session
Write-Host ""
Write-Host "Step 7: Clearing port 8000 (previous Uvicorn)..." -ForegroundColor Yellow
$port = 8000
try {
    $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($conns) {
        $pids = $conns.OwningProcess | Sort-Object -Unique
        foreach ($pid in $pids) {
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
            Write-Host "  Stopped process on port $port (PID $pid)" -ForegroundColor Gray
        }
    }
} catch {
    $line = netstat -ano | findstr ":$port "
    if ($line) {
        $parts = $line.Trim() -split '\s+'
        $pid = $parts[-1]
        if ($pid -match '^\d+$') {
            taskkill /PID $pid /F 2>$null
            Write-Host "  Stopped process on port $port (PID $pid)" -ForegroundColor Gray
        }
    }
}
Start-Sleep -Seconds 1
Write-Host "OK Port 8000 cleared" -ForegroundColor Green

# Step 8: ใช้ ngrok ที่รันอยู่แล้วถ้ามี (บัญชีฟรีจำกัด 1 session) ไม่ก็สตาร์ทใหม่
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$ngrokUrl = $null
if (Get-Command ngrok -ErrorAction SilentlyContinue) {
    # ถ้า port 4040 ถูกใช้ = มี ngrok รันอยู่แล้ว → ใช้ tunnel เดิม (ไม่สตาร์ทซ้ำ จะได้ไม่โดน ERR_NGROK_108)
    $ngrokAlreadyRunning = $false
    try {
        $tunnels = Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels" -ErrorAction Stop
        $https = $tunnels.tunnels | Where-Object { $_.public_url -like "https://*" } | Select-Object -First 1
        if ($https -and $https.public_url) {
            $ngrokUrl = $https.public_url.TrimEnd("/")
            $ngrokAlreadyRunning = $true
            Write-Host "Using existing ngrok tunnel: $ngrokUrl" -ForegroundColor Green
        }
    } catch { }

    if (-not $ngrokAlreadyRunning) {
        Write-Host "Starting ngrok (port 8000)..." -ForegroundColor Yellow
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
                    Write-Host "ngrok API not ready in time. If you see ERR_NGROK_108, close any other ngrok window and run this script again." -ForegroundColor Yellow
                }
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
Write-Host ""
Write-Host "ถ้าเปิดลิงก์ไม่ได้ (ERR_NGROK_3200 / ERR_NGROK_727): ใช้ localhost แทน -> " -ForegroundColor Yellow -NoNewline
Write-Host "http://localhost:8000/launch?store_id=1" -ForegroundColor Cyan
