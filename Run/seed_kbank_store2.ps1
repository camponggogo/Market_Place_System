# ใส่ข้อมูล K Bank (K API จาก K_API.note) เข้า store_id=2

$root = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $root

Write-Host "Seed K Bank config -> store_id=2 ..." -ForegroundColor Cyan
python code/scripts/seed_kbank_store2.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Done." -ForegroundColor Green
