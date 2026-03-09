# รัน migration เพิ่มคอลัมน์ Member ในตาราง customers (username, email, password_hash, total_points, updated_at)
# ใช้เมื่อ seed_members.py แจ้ง "ตาราง customers ยังไม่มีคอลัมน์สำหรับ Member"
# รันจากโฟลเดอร์โปรเจกต์: .\Run\run_migrate_customers_member.ps1

$root = if ($PSScriptRoot) { Split-Path -Parent $PSScriptRoot } else { Get-Location }
Set-Location $root

$relSql = "Run\migrate_customers_member.sql"
if (-not (Test-Path $relSql)) {
    Write-Host "ไม่พบไฟล์ $relSql (รันจากโฟลเดอร์โปรเจกต์)" -ForegroundColor Red
    exit 1
}

Write-Host "กำลังรัน migration: migrate_customers_member.sql" -ForegroundColor Yellow
Write-Host "จะถามรหัสผ่าน MySQL (user root, database market_place_system)" -ForegroundColor Gray
# ใน PowerShell ใช้ cmd /c เพื่อให้ < redirect ทำงาน (ใน PowerShell ตัว < ไม่ใช้กับไฟล์)
cmd /c "mysql -u root -p 123456 market_place_system < $relSql"
if ($LASTEXITCODE -eq 0) {
    Write-Host "Migration เสร็จแล้ว — รัน python Run/seed_members.py ได้เลย" -ForegroundColor Green
} else {
    Write-Host "ถ้า error Duplicate column / Duplicate key แปลว่ามีคอลัมน์แล้ว ไม่ต้องรันซ้ำ" -ForegroundColor Gray
    exit $LASTEXITCODE
}
