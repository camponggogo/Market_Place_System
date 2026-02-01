@echo off
REM Script สำหรับสร้าง Virtual Environment บน Windows

echo Creating virtual environment...
python -m venv venv

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Upgrading pip...
python -m pip install --upgrade pip

echo Installing dependencies...
pip install -r requirements.txt

echo.
echo ========================================
echo Virtual environment setup complete!
echo.
echo To activate the virtual environment, run:
echo   venv\Scripts\activate
echo.
echo To run the application:
echo   uvicorn main:app --reload
echo ========================================

pause

