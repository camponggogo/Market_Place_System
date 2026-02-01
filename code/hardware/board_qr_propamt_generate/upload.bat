@echo off
REM Upload firmware to ESP8266 D1 Mini Pro on COM4
REM Requires: Arduino CLI (install from https://arduino.github.io/arduino-cli/installation/)

set SKETCH_DIR=%~dp0
set SKETCH=%SKETCH_DIR%board_qr_propamt_generate.ino
set FQBN=esp8266:esp8266:d1_mini_pro
set PORT=COM4

where arduino-cli >nul 2>&1
if %ERRORLEVEL% neq 0 (
  echo Arduino CLI not found in PATH.
  echo.
  echo Option 1 - Install Arduino CLI then run this script again:
  echo   https://arduino.github.io/arduino-cli/installation/
  echo.
  echo Option 2 - Use Arduino IDE:
  echo   1. Open the sketch
  echo   2. Tools - Board - ESP8266 Boards - LOLIN D1 mini Pro
  echo   3. Tools - Port - COM4
  echo   4. Click Upload - arrow button
  echo.
  start "" "C:\Program Files\Arduino IDE\Arduino IDE.exe" "%SKETCH%"
  exit /b 1
)

echo Compiling...
arduino-cli compile --fqbn %FQBN% "%SKETCH_DIR%"
if %ERRORLEVEL% neq 0 (
  echo Compile failed.
  exit /b 1
)

echo Uploading to %PORT%...
arduino-cli upload -p %PORT% --fqbn %FQBN% "%SKETCH_DIR%"
if %ERRORLEVEL% neq 0 (
  echo Upload failed. Check that board is on COM4 and in boot mode.
  exit /b 1
)

echo Done.
exit /b 0
