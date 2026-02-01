#!/bin/bash
# Quick Start Script for Linux/Mac
# Food Court Management System

echo "============================================================"
echo "Food Court Management System - Quick Start"
echo "============================================================"
echo ""

# Step 1: Check Python
echo "Step 1: Checking Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "✅ Python found: $PYTHON_VERSION"
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version)
    echo "✅ Python found: $PYTHON_VERSION"
    PYTHON_CMD=python
else
    echo "❌ Python not found! Please install Python 3.12+"
    exit 1
fi

# Step 2: Install Dependencies
echo ""
echo "Step 2: Installing dependencies..."
$PYTHON_CMD -m pip install --upgrade pip
$PYTHON_CMD -m pip install -r requirements.txt
if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed"
else
    echo "⚠️  Some dependencies may have conflicts"
fi

# Step 3: Check Setup
echo ""
echo "Step 3: Checking setup..."
$PYTHON_CMD scripts/check_setup.py
if [ $? -ne 0 ]; then
    echo "⚠️  Setup check found issues"
fi

# Step 4: Create Database
echo ""
echo "Step 4: Creating database..."
$PYTHON_CMD scripts/create_database.py
if [ $? -ne 0 ]; then
    echo "⚠️  Database creation had issues"
fi

# Step 5: Initialize Database
echo ""
echo "Step 5: Initializing database..."
$PYTHON_CMD scripts/init_db.py
if [ $? -eq 0 ]; then
    echo "✅ Database initialized"
else
    echo "❌ Database initialization failed"
    exit 1
fi

# Step 6: Create Sample Data
echo ""
echo "Step 6: Creating sample data (20 items)..."
read -p "Do you want to create sample data? (Y/N): " create_sample
if [ "$create_sample" = "Y" ] || [ "$create_sample" = "y" ]; then
    $PYTHON_CMD scripts/create_sample_data.py
    if [ $? -eq 0 ]; then
        echo "✅ Sample data created"
    fi
fi

# Step 7: Start Server
echo ""
echo "============================================================"
echo "Setup Complete!"
echo "============================================================"
echo ""
echo "To start the server, run:"
echo "  uvicorn main:app --reload"
echo ""
echo "Then open:"
echo "  http://localhost:8000/docs - API Documentation"
echo "  http://localhost:8000/static/index.html - Customer Interface"
echo ""

read -p "Do you want to start the server now? (Y/N): " start_server
if [ "$start_server" = "Y" ] || [ "$start_server" = "y" ]; then
    echo ""
    echo "Starting server..."
    echo "Press Ctrl+C to stop"
    echo ""
    uvicorn main:app --reload
fi

