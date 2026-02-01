@echo off
setlocal

REM Kill any process listening on port 8001 (best-effort)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8001') do (
  taskkill /PID %%a /F >nul 2>nul
)

REM Start the QR web server in a new minimized window
start "PromptPay QR Debug" /MIN python scripts\qr_code_web.py

endlocal

