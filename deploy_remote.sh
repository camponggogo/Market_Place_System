#!/bin/bash

# Remote Deployment Script
# Deploys Food Court Management System to remote server via SSH

set -e

# Configuration
REMOTE_HOST="150.95.85.185"
REMOTE_USER="root"
REMOTE_PASS="P@ssw0rd@dev"
REMOTE_DIR="/opt/foodcourt"
LOCAL_DIR="."

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=========================================="
echo "Food Court Management System"
echo "Remote Deployment Script"
echo "=========================================="
echo "Target: ${REMOTE_USER}@${REMOTE_HOST}"
echo "Directory: ${REMOTE_DIR}"
echo "=========================================="

# Check if rsync is available
if ! command -v rsync &> /dev/null; then
    echo -e "${RED}Error: rsync is not installed${NC}"
    echo "Install rsync or use SCP/SCP alternative"
    exit 1
fi

# Check if sshpass is available (for password authentication)
USE_SSHPASS=false
if command -v sshpass &> /dev/null; then
    USE_SSHPASS=true
fi

# Function to run remote command
run_remote() {
    if [ "$USE_SSHPASS" = true ]; then
        sshpass -p "$REMOTE_PASS" ssh -o StrictHostKeyChecking=no "${REMOTE_USER}@${REMOTE_HOST}" "$1"
    else
        ssh -o StrictHostKeyChecking=no "${REMOTE_USER}@${REMOTE_HOST}" "$1"
    fi
}

# Function to copy files
copy_files() {
    echo "Uploading files to server..."
    if [ "$USE_SSHPASS" = true ]; then
        sshpass -p "$REMOTE_PASS" rsync -avz --progress \
            --exclude 'venv' \
            --exclude '__pycache__' \
            --exclude '.git' \
            --exclude '*.pyc' \
            --exclude '.pytest_cache' \
            --exclude 'htmlcov' \
            --exclude '*.db' \
            --exclude '*.sqlite' \
            --exclude '.env' \
            "${LOCAL_DIR}/" "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/"
    else
        rsync -avz --progress \
            --exclude 'venv' \
            --exclude '__pycache__' \
            --exclude '.git' \
            --exclude '*.pyc' \
            --exclude '.pytest_cache' \
            --exclude 'htmlcov' \
            --exclude '*.db' \
            --exclude '*.sqlite' \
            --exclude '.env' \
            "${LOCAL_DIR}/" "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/"
    fi
}

# Check Docker installation on remote
echo "Checking Docker installation on remote server..."
if ! run_remote "command -v docker &> /dev/null"; then
    echo -e "${YELLOW}Docker not found. Installing Docker...${NC}"
    run_remote "curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh && systemctl start docker && systemctl enable docker"
fi

# Check Docker Compose
if ! run_remote "docker compose version &> /dev/null && docker-compose version &> /dev/null"; then
    echo -e "${YELLOW}Docker Compose not found. Installing...${NC}"
    run_remote "apt-get update && apt-get install -y docker-compose-plugin || curl -L 'https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)' -o /usr/local/bin/docker-compose && chmod +x /usr/local/bin/docker-compose"
fi

echo -e "${GREEN}✓ Docker is ready${NC}"

# Create remote directory
echo "Creating remote directory..."
run_remote "mkdir -p ${REMOTE_DIR}"

# Upload files
copy_files

# Create .env if not exists
echo "Setting up environment..."
run_remote "cd ${REMOTE_DIR} && if [ ! -f .env ]; then cp .env.example .env 2>/dev/null || echo 'Please create .env file manually'; fi"

# Run deployment on remote
echo "Running deployment on remote server..."
run_remote "cd ${REMOTE_DIR} && chmod +x deploy.sh && ./deploy.sh production"

echo ""
echo -e "${GREEN}=========================================="
echo "Deployment completed!"
echo "==========================================${NC}"
echo ""
echo "Application URLs:"
echo "  - Main: http://${REMOTE_HOST}"
echo "  - Admin: http://${REMOTE_HOST}/admin"
echo "  - Health: http://${REMOTE_HOST}/health"
echo ""
echo "To view logs:"
echo "  ssh ${REMOTE_USER}@${REMOTE_HOST}"
echo "  cd ${REMOTE_DIR}"
echo "  docker compose logs -f"
echo ""

