# Seed ข้อมูลตัวอย่าง + scb.note ลง database market_place_system @ localhost (ทดสอบ full-loop)
# ต้องมี MySQL/MariaDB รันอยู่ที่ localhost, user/password ตาม config.ini (หรือ env)

$root = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $root

Write-Host "Seed Full Sample -> market_place_system @ localhost ..." -ForegroundColor Cyan
python code/scripts/seed_full_sample.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host ""
Write-Host "ตั้ง config.ini: DB_NAME=market_place_system แล้วรัน backend (quick_start.ps1) เพื่อทดสอบ full-loop" -ForegroundColor Yellow
Write-Host "Done." -ForegroundColor Green
