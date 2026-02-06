# ใส่ข้อมูล SCB PromptPay (จาก scb.note) เข้า store_id=2 ในฐานข้อมูล
# รันจากโฟลเดอร์ Run หรือ project root

$root = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $root

Write-Host "Seed SCB config -> store_id=2 ..." -ForegroundColor Cyan
python code/scripts/seed_scb_store2.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Done." -ForegroundColor Green
