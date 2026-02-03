@echo off
REM Radar Configuration Dashboard - Startup Script (Windows)

cd /d "%~dp0"

echo Radar Configuration Dashboard - Roma
echo ======================================

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Check if dependencies are installed
python -c "import flask" 2>nul
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

REM Run the application
python run.py

pause
