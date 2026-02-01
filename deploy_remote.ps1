# Remote Deployment Script for Windows PowerShell
# Deploys Food Court Management System to remote server via SSH

param(
    [string]$RemoteHost = "150.95.85.185",
    [string]$RemoteUser = "root",
    [string]$RemotePass = "P@ssw0rd@dev",
    [string]$RemoteDir = "/opt/foodcourt",
    [string]$LocalDir = "."
)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Food Court Management System" -ForegroundColor Cyan
Write-Host "Remote Deployment Script (PowerShell)" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Target: ${RemoteUser}@${RemoteHost}" -ForegroundColor Yellow
Write-Host "Directory: ${RemoteDir}" -ForegroundColor Yellow
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if SSH is available
if (-not (Get-Command ssh -ErrorAction SilentlyContinue)) {
    Write-Host "Error: SSH is not available. Please install OpenSSH or use Git Bash." -ForegroundColor Red
    exit 1
}

# Function to run remote command
function Invoke-RemoteCommand {
    param([string]$Command)
    
    $sshCommand = "ssh -o StrictHostKeyChecking=no ${RemoteUser}@${RemoteHost} `"$Command`""
    Invoke-Expression $sshCommand
}

# Check Docker installation on remote
Write-Host "Checking Docker installation on remote server..." -ForegroundColor Yellow
try {
    $dockerCheck = Invoke-RemoteCommand "command -v docker"
    if (-not $dockerCheck) {
        Write-Host "Docker not found. Installing Docker..." -ForegroundColor Yellow
        Invoke-RemoteCommand "curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh && systemctl start docker && systemctl enable docker"
    }
} catch {
    Write-Host "Warning: Could not check Docker installation" -ForegroundColor Yellow
}

Write-Host "Docker is ready" -ForegroundColor Green

# Create remote directory
Write-Host "Creating remote directory..." -ForegroundColor Yellow
Invoke-RemoteCommand "mkdir -p ${RemoteDir}"

# Upload files using SCP
Write-Host "Uploading files to server..." -ForegroundColor Yellow
Write-Host "Note: This may take a while. Large files and directories will be excluded." -ForegroundColor Gray

# Exclude patterns
$excludePatterns = @(
    "venv",
    "__pycache__",
    ".git",
    "*.pyc",
    ".pytest_cache",
    "htmlcov",
    "*.db",
    "*.sqlite",
    ".env"
)

# Create temporary exclude file
$excludeFile = [System.IO.Path]::GetTempFileName()
$excludePatterns | ForEach-Object { Add-Content -Path $excludeFile -Value $_ }

# Use rsync if available (via WSL or Git Bash), otherwise use SCP
if (Get-Command rsync -ErrorAction SilentlyContinue) {
    $excludeArgs = $excludePatterns | ForEach-Object { "--exclude=$_" }
    $rsyncCommand = "rsync -avz --progress $($excludeArgs -join ' ') ${LocalDir}/ ${RemoteUser}@${RemoteHost}:${RemoteDir}/"
    Invoke-Expression $rsyncCommand
} else {
    Write-Host "rsync not found. Using SCP (slower, but will work)..." -ForegroundColor Yellow
    Write-Host "Note: For better performance, install rsync or use Git Bash" -ForegroundColor Gray
    
    # Simple SCP - will copy everything (you may want to manually exclude large dirs)
    $scpCommand = "scp -r ${LocalDir}/* ${RemoteUser}@${RemoteHost}:${RemoteDir}/"
    Write-Host "Running: $scpCommand" -ForegroundColor Gray
    Invoke-Expression $scpCommand
}

# Remove temp file
Remove-Item $excludeFile -ErrorAction SilentlyContinue

# Create .env if not exists
Write-Host "Setting up environment..." -ForegroundColor Yellow
Invoke-RemoteCommand "cd ${RemoteDir} && if [ ! -f .env ]; then cp .env.example .env 2>/dev/null || echo 'Please create .env file manually'; fi"

# Run deployment on remote
Write-Host "Running deployment on remote server..." -ForegroundColor Yellow
Invoke-RemoteCommand "cd ${RemoteDir} && chmod +x deploy.sh && ./deploy.sh production"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "Deployment completed!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Application URLs:" -ForegroundColor Cyan
Write-Host "  - Main: http://${RemoteHost}" -ForegroundColor White
Write-Host "  - Admin: http://${RemoteHost}/admin" -ForegroundColor White
Write-Host "  - Health: http://${RemoteHost}/health" -ForegroundColor White
Write-Host ""
Write-Host "To view logs:" -ForegroundColor Cyan
Write-Host "  ssh ${RemoteUser}@${RemoteHost}" -ForegroundColor White
Write-Host "  cd ${RemoteDir}" -ForegroundColor White
Write-Host "  docker compose logs -f" -ForegroundColor White
Write-Host ""

