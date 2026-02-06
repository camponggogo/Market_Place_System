# เปิด Front-end (Customer, Store-POS, Admin, Signage) ใน Browser
# ต้องรัน Back-end ก่อน: .\Run\start_backend.ps1

$root = (Get-Item $PSScriptRoot).Parent.FullName
$base = "http://localhost:8000"
$storeId = 1

Write-Host "Opening Front-end (Back-end must be running at $base)..." -ForegroundColor Cyan
Write-Host "  Admin:     $base/admin" -ForegroundColor Gray
Write-Host "  Store-POS: $base/store-pos?store_id=$storeId" -ForegroundColor Gray
Write-Host "  Signage:   $base/signage?store_id=$storeId" -ForegroundColor Gray
Write-Host "  Customer:  $base/customer" -ForegroundColor Gray
Write-Host "  Launch:    $base/launch?store_id=$storeId (POS + Signage)" -ForegroundColor Gray
Write-Host ""

Start-Process "$base/admin"
Start-Sleep -Milliseconds 400
Start-Process "$base/store-pos?store_id=$storeId"
Start-Sleep -Milliseconds 400
Start-Process "$base/signage?store_id=$storeId"
Start-Sleep -Milliseconds 400
Start-Process "$base/customer"

Write-Host "Done. Close browser tabs to exit." -ForegroundColor Green
