#!/bin/bash

# Food Court Management System - Docker Deployment Script
# Usage: ./deploy.sh [production|staging]

set -e

ENVIRONMENT=${1:-production}
PROJECT_NAME="foodcourt"
COMPOSE_FILE="docker-compose.yml"

echo "=========================================="
echo "Food Court Management System"
echo "Docker Deployment Script"
echo "Environment: $ENVIRONMENT"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    exit 1
fi

# Use docker compose (v2) if available, otherwise docker-compose (v1)
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

echo -e "${GREEN}✓ Docker and Docker Compose are installed${NC}"

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Warning: .env file not found. Creating from .env.example...${NC}"
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${YELLOW}Please edit .env file with your configuration before continuing${NC}"
        read -p "Press Enter to continue after editing .env file..."
    else
        echo -e "${RED}Error: .env.example not found${NC}"
        exit 1
    fi
fi

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p nginx/ssl
mkdir -p logs
mkdir -p data

# Stop existing containers
echo "Stopping existing containers..."
$COMPOSE_CMD down || true

# Pull latest images (if using pre-built images)
# echo "Pulling latest images..."
# $COMPOSE_CMD pull

# Build Docker images
echo "Building Docker images..."
$COMPOSE_CMD build --no-cache

# Start services
echo "Starting services..."
$COMPOSE_CMD up -d

# Wait for database to be ready
echo "Waiting for database to be ready..."
sleep 10

# Check if database is healthy
DB_HEALTHY=false
for i in {1..30}; do
    if docker exec foodcourt_db mysqladmin ping -h localhost -u root -p${DB_ROOT_PASSWORD:-P@ssw0rd@dev} --silent; then
        DB_HEALTHY=true
        break
    fi
    echo "Waiting for database... ($i/30)"
    sleep 2
done

if [ "$DB_HEALTHY" = false ]; then
    echo -e "${RED}Error: Database failed to start${NC}"
    $COMPOSE_CMD logs db
    exit 1
fi

echo -e "${GREEN}✓ Database is ready${NC}"

# Initialize database (create tables)
echo "Initializing database..."
docker exec foodcourt_app python -c "
from app.database import engine, Base
from app.models import *
Base.metadata.create_all(bind=engine)
print('Database tables created successfully!')
" || {
    echo -e "${YELLOW}Warning: Database initialization had issues. Check logs.${NC}"
}

# Or use init script if available
if [ -f scripts/init_db.py ]; then
    echo "Running database initialization script..."
    docker exec foodcourt_app python scripts/init_db.py || {
        echo -e "${YELLOW}Warning: Init script had issues. Check logs.${NC}"
    }
fi

# Check application health
echo "Checking application health..."
sleep 5

APP_HEALTHY=false
for i in {1..20}; do
    if curl -f http://localhost:8000/health &> /dev/null; then
        APP_HEALTHY=true
        break
    fi
    echo "Waiting for application... ($i/20)"
    sleep 2
done

if [ "$APP_HEALTHY" = false ]; then
    echo -e "${RED}Error: Application failed to start${NC}"
    $COMPOSE_CMD logs app
    exit 1
fi

echo -e "${GREEN}✓ Application is ready${NC}"

# Show status
echo ""
echo "=========================================="
echo -e "${GREEN}Deployment completed successfully!${NC}"
echo "=========================================="
echo ""
echo "Services:"
$COMPOSE_CMD ps
echo ""
echo "Application URLs:"
echo "  - Main: http://150.95.85.185"
echo "  - Admin: http://150.95.85.185/admin"
echo "  - Health: http://150.95.85.185/health"
echo ""
echo "Useful commands:"
echo "  - View logs: $COMPOSE_CMD logs -f"
echo "  - Stop services: $COMPOSE_CMD down"
echo "  - Restart services: $COMPOSE_CMD restart"
echo "  - View status: $COMPOSE_CMD ps"
echo ""

