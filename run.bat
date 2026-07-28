@echo off
echo === Zenith Launcher ===

:: Check Python version
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH. Please install Python 3.12+ to play Zenith.
    pause
    exit /b 1
)

:: Set up virtual environment
if not exist ".venv" if not exist "venv" (
    echo Creating virtual environment ^(.venv^)...
    python -m venv .venv
)

:: Activate virtual environment
if exist ".venv" (
    call .venv\Scripts\activate.bat
) else if exist "venv" (
    call venv\Scripts\activate.bat
)

:: Install dependencies
echo Installing dependencies...
python -m pip install --upgrade pip
pip install pygame-ce

:: Run game
echo Launching Zenith...
python main.py
pause
