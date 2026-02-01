# Production Server Startup Script for Windows PowerShell
# Note: Gunicorn ไม่รองรับ Windows ใช้ Uvicorn หรือ Hypercorn แทน

Write-Host "Starting Food Court Management System in Production Mode..." -ForegroundColor Cyan
Write-Host ""

# Option 1: Uvicorn with multiple workers (แนะนำสำหรับ Windows)
Write-Host "Using Uvicorn with 4 workers (Windows compatible)..." -ForegroundColor Yellow
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# Option 2: Hypercorn (เร็วกว่า, รองรับ HTTP/2, รองรับ Windows)
# Write-Host "Using Hypercorn (Windows compatible)..." -ForegroundColor Yellow
# hypercorn main:app --bind 0.0.0.0:8000 --workers 4

# Option 3: Uvicorn single worker (สำหรับ development)
# Write-Host "Using Uvicorn (single worker)..." -ForegroundColor Yellow
# uvicorn main:app --host 0.0.0.0 --port 8000 --reload

