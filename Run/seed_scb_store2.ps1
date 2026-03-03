# ใส่ข้อมูล SCB PromptPay (จาก scb.note) เข้า store ในฐานข้อมูล
# รัน: .\Run\seed_scb_store2.ps1 [store_id]
# ถ้าไม่ระบุ store_id จะใส่ทั้ง store 1 และ 2 (สำหรับ launch?store_id=1)

$root = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $root

$storeId = $args[0]
if ($storeId) {
    Write-Host "Seed SCB config -> store_id=$storeId ..." -ForegroundColor Cyan
    python code/scripts/seed_scb_store2.py $storeId
} else {
    Write-Host "Seed SCB config -> store_id=1, 2 ..." -ForegroundColor Cyan
    python code/scripts/seed_scb_store2.py 1
    python code/scripts/seed_scb_store2.py 2
}
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Done." -ForegroundColor Green
