#!/bin/bash
# Script สำหรับสร้าง Virtual Environment บน Linux/Mac

echo "Creating virtual environment..."
python3 -m venv venv

echo "Activating virtual environment..."
source venv/bin/activate

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "========================================"
echo "Virtual environment setup complete!"
echo ""
echo "To activate the virtual environment, run:"
echo "  source venv/bin/activate"
echo ""
echo "To run the application:"
echo "  uvicorn main:app --reload"
echo "========================================"

