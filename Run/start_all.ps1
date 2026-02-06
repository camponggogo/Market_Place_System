# รัน Back-end แล้วเปิด Front-end (Customer, Store-POS, Admin, Signage) ใน Browser
# รวมการรันให้ทำงานสอดประสาน: Back-end [DB + API Bank + Webhook SCB/K Bank] + เปิดหน้าจอ Front-end

$root = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $root
$env:PYTHONPATH = "$root\code"

$port = 8000
$base = "http://localhost:$port"
$storeId = 1

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Start All: Back-end + Front-end (Customer, Store-POS, Admin)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Starting Back-end (port $port)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$root'; `$env:PYTHONPATH='$root\code'; uvicorn main:app --reload --host 0.0.0.0 --port $port"
Write-Host "Waiting for server..." -ForegroundColor Gray
Start-Sleep -Seconds 5
Write-Host "Opening Front-end..." -ForegroundColor Yellow
Start-Process "$base/admin"
Start-Sleep -Milliseconds 500
Start-Process "$base/store-pos?store_id=$storeId"
Start-Sleep -Milliseconds 500
Start-Process "$base/signage?store_id=$storeId"
Start-Sleep -Milliseconds 500
Start-Process "$base/launch?store_id=$storeId"
Write-Host ""
Write-Host "Back-end is running in the other window. Front-end opened in browser." -ForegroundColor Green
Write-Host "Webhook: SCB $base/api/payment-callback/webhook | K Bank $base/api/payment-callback/webhook/kbank" -ForegroundColor Gray
