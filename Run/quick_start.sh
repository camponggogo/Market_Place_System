#!/bin/bash
# Quick Start Script for Linux/Mac
# Market_Place_System - โครงสร้าง: README (root), code/, Run/, Deploy/

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT/code"

echo "============================================================"
echo "Market_Place_System - Quick Start"
echo "============================================================"
echo ""

# Step 1: Check Python
echo "Step 1: Checking Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "OK Python found: $PYTHON_VERSION"
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version)
    echo "OK Python found: $PYTHON_VERSION"
    PYTHON_CMD=python
else
    echo "Python not found! Please install Python 3.12+"
    exit 1
fi

# Step 2: Install Dependencies
echo ""
echo "Step 2: Installing dependencies (code/)..."
$PYTHON_CMD -m pip install --upgrade pip
$PYTHON_CMD -m pip install -r code/requirements.txt
if [ $? -eq 0 ]; then
    echo "OK Dependencies installed"
else
    echo "Some dependencies may have conflicts"
fi

# Step 3: Check Setup
echo ""
echo "Step 3: Checking setup..."
$PYTHON_CMD Run/check_setup.py
if [ $? -ne 0 ]; then
    echo "Setup check found issues"
fi

# Step 4: Create Database
echo ""
echo "Step 4: Creating database..."
$PYTHON_CMD Run/create_database.py
if [ $? -ne 0 ]; then
    echo "Database creation had issues"
fi

# Step 5: Initialize Database
echo ""
echo "Step 5: Initializing database..."
$PYTHON_CMD Run/init_db.py
if [ $? -eq 0 ]; then
    echo "OK Database initialized"
else
    echo "Database initialization failed"
    exit 1
fi

# Step 6: Create Sample Data
echo ""
echo "Step 6: Creating sample data..."
$PYTHON_CMD Run/create_sample_data.py
if [ $? -eq 0 ]; then
    echo "OK Sample data created"
fi

# Step 7: Start Server
echo ""
echo "============================================================"
echo "Setup Complete!"
echo "============================================================"
echo ""
echo "To start the server (from project root):"
echo "  PYTHONPATH=code uvicorn main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "Then open:"
echo "  http://localhost:8000/docs - API Documentation"
echo "  http://localhost:8000/launch?store_id=1 - Store POS + Signage"
echo ""

read -p "Start the server now? (Y/N): " start_server
if [ "$start_server" = "Y" ] || [ "$start_server" = "y" ]; then
    echo ""
    echo "Starting server... Press Ctrl+C to stop"
    echo ""
    PYTHONPATH="$ROOT/code" uvicorn main:app --reload --host 0.0.0.0 --port 8000
fi
