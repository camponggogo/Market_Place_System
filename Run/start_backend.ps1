# รัน Back-end เท่านั้น: FastAPI (Database, API Bank, Webhook SCB + K Bank PromptPay)
# ต้องรันก่อน แล้วค่อยเปิด Front-end (start_frontend.ps1) หรือเปิด Browser เอง

$root = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $root
$env:PYTHONPATH = "$root\code"

$port = 8000
$hostUrl = "http://localhost:$port"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Back-end (Database + API + Webhook SCB / K Bank)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host " API & Docs:  $hostUrl/docs" -ForegroundColor White
Write-Host " Health:      $hostUrl/health" -ForegroundColor White
Write-Host ""
Write-Host " Webhook ลงทะเบียนกับธนาคาร (ใช้ URL จริงใน production):" -ForegroundColor Yellow
Write-Host "   SCB:    POST $hostUrl/api/payment-callback/webhook" -ForegroundColor Gray
Write-Host "   K Bank: POST $hostUrl/api/payment-callback/webhook/kbank" -ForegroundColor Gray
Write-Host ""
Write-Host " หลัง Back-end รันแล้ว เปิด Front-end: .\Run\start_frontend.ps1" -ForegroundColor Yellow
Write-Host ""

uvicorn main:app --reload --host 0.0.0.0 --port $port
