@echo off
cd /d "%~dp0"

REM Check Python environment
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python interpreter not found. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

REM Check dependencies
echo Checking dependencies...
python -c "import streamlit" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Installing dependencies...
    python -m pip install -r requirements.txt
)

REM Start application
echo Starting RiverInfos application...
python -m streamlit run app.py
pause 