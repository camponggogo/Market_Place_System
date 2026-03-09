# Copy โปรเจกต์ไปเซิร์ฟเวอร์ (150.95.85.185) ด้วย SCP แล้วรัน Docker ทันที
# ใช้: จาก root โปรเจกต์ (Marketplace) → .\Deploy\deploy_to_campong.ps1
# ต้องมี: OpenSSH (scp, ssh) ใน PATH
# ถ้า Connection timed out: ตรวจสอบ firewall/พอร์ต หรือใช้ -RemoteSshPort ถ้า SSH ไม่ใช้พอร์ต 22

param(
    [string]$RemoteHost = "150.95.85.185",
    [string]$RemoteUser = "admin",
    [string]$RemoteDir = "/opt/marketplace",
    [int]$RemoteSshPort = 22
)

$ErrorActionPreference = "Stop"
# โปรเจกต์ root = โฟลเดอร์ที่มี code, Run, Deploy (parent ของ Deploy)
$ProjectRoot = Resolve-Path "$PSScriptRoot\.."
Set-Location $ProjectRoot

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Deploy to m.campong.co.th (Docker)" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Project root: $ProjectRoot"
Write-Host "Target: ${RemoteUser}@${RemoteHost}:${RemoteDir} (SSH port: $RemoteSshPort)"
Write-Host "==========================================" -ForegroundColor Cyan

# ssh ใช้ -p (ตัวเล็ก), scp ใช้ -P (ตัวใหญ่) สำหรับพอร์ต
$sshPortOpt = @(); if ($RemoteSshPort -ne 22) { $sshPortOpt = @("-p", $RemoteSshPort) }
$scpPortOpt = @(); if ($RemoteSshPort -ne 22) { $scpPortOpt = @("-P", $RemoteSshPort) }
$sshCommon = @("-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=15")
$sshArgs = $sshPortOpt + $sshCommon

if (-not (Get-Command scp -ErrorAction SilentlyContinue)) {
    Write-Host "Error: scp not found. Install OpenSSH Client (optional feature on Windows)." -ForegroundColor Red
    exit 1
}
if (-not (Get-Command ssh -ErrorAction SilentlyContinue)) {
    Write-Host "Error: ssh not found. Install OpenSSH Client." -ForegroundColor Red
    exit 1
}

# 1) สร้างโฟลเดอร์บน remote
Write-Host "Creating remote directory..." -ForegroundColor Yellow
& ssh @sshArgs "${RemoteUser}@${RemoteHost}" "mkdir -p ${RemoteDir}"

# 2) SCP โฟลเดอร์ code, Run, Deploy (ทั้งโฟลเดอร์; ถ้ามี WSL/Git Bash ใช้ deploy_to_campong.sh จะเร็วกว่าและ exclude ได้)
$scpCommon = @("-r", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=15")
$scpArgs = $scpPortOpt + $scpCommon

Write-Host "Uploading code/..." -ForegroundColor Yellow
& scp @scpArgs "$ProjectRoot\code" "${RemoteUser}@${RemoteHost}:${RemoteDir}/"

Write-Host "Uploading Run/..." -ForegroundColor Yellow
& scp @scpArgs "$ProjectRoot\Run" "${RemoteUser}@${RemoteHost}:${RemoteDir}/"

Write-Host "Uploading Deploy/..." -ForegroundColor Yellow
& scp @scpArgs "$ProjectRoot\Deploy" "${RemoteUser}@${RemoteHost}:${RemoteDir}/"

if (Test-Path "$ProjectRoot\.env.example") {
    Write-Host "Uploading .env.example..." -ForegroundColor Yellow
    $scpFileArgs = $scpPortOpt + @("-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=15")
    & scp @scpFileArgs "$ProjectRoot\.env.example" "${RemoteUser}@${RemoteHost}:${RemoteDir}/Deploy/.env.example"
}

# 3) SSH เข้าไปรัน Docker
Write-Host "Starting Docker on remote..." -ForegroundColor Green
$remoteCmd = @"
set -e
cd ${RemoteDir}/Deploy
[ -f .env ] || { [ -f .env.example ] && cp .env.example .env; } || true
chmod +x deploy.sh certbot-init.sh certbot-renew.sh 2>/dev/null || true
if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  docker compose -f docker-compose.yml down 2>/dev/null || true
  docker compose -f docker-compose.yml build --no-cache
  docker compose -f docker-compose.yml up -d
  echo 'Waiting for services...'
  sleep 15
  docker compose -f docker-compose.yml ps
else
  ./deploy.sh production
fi
"@
& ssh @sshArgs "${RemoteUser}@${RemoteHost}" $remoteCmd

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "Deploy done." -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host "URL: https://${RemoteHost}:639 (or https://m.campong.co.th:639)"
Write-Host "Health: https://${RemoteHost}:639/health"
Write-Host ""
Write-Host "View logs: ssh ${RemoteUser}@${RemoteHost} 'cd ${RemoteDir}/Deploy && docker compose logs -f'"
Write-Host ""
