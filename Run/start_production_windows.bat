@echo off
REM Production Server Startup Script for Windows
REM Note: Gunicorn ไม่รองรับ Windows ใช้ Uvicorn หรือ Hypercorn แทน

echo ========================================
echo Food Court Management System
echo Production Mode (Windows)
echo ========================================
echo.

echo Starting server with Uvicorn (4 workers)...
echo Press Ctrl+C to stop
echo.

uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

pause

