#!/bin/bash
# Production Server Startup Script (Linux/Unix/Mac)

echo "Starting Food Court Management System in Production Mode..."

# Detect OS
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "⚠️  Windows detected! Gunicorn ไม่รองรับ Windows"
    echo "Using Uvicorn instead..."
    uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
    exit 0
fi

# Option 1: Gunicorn + Uvicorn Workers (แนะนำสำหรับ Linux/Unix/Mac)
echo "Using Gunicorn + Uvicorn Workers..."
gunicorn main:app -c gunicorn_config.py

# Option 2: Hypercorn (เร็วกว่า, รองรับ HTTP/2)
# echo "Using Hypercorn..."
# hypercorn main:app --config hypercorn_config.py

# Option 3: Uvicorn with multiple workers (fallback)
# echo "Using Uvicorn with workers..."
# uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

