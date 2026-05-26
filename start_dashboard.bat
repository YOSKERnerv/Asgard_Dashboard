@echo off
REM ASGARD Dashboard Startup Script

echo.
echo ============================================
echo   ASGARD Alliance Dashboard Startup
echo ============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Start the Flask app
echo.
echo Starting Flask server...
echo.
echo Dashboard URL: http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo.

python flask_app.py
