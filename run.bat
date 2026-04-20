@echo off
REM OHM - Oral History Manager - Windows Launch Script
REM Sets up a Python virtual environment and launches the Flet app.
REM
REM Prerequisites (one-time, if not already installed):
REM   Python 3:  https://www.python.org/downloads/
REM   ffmpeg:    https://ffmpeg.org/download.html  (add to PATH)

setlocal EnableDelayedExpansion
cd /d "%~dp0"

echo === OHM - Oral History Manager ===
echo.

REM Verify Python is available
where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found on PATH.
    echo Please install Python 3 from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist ".venv\" (
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat
echo [OK] Virtual environment activated
echo.

REM Install / upgrade dependencies
echo Installing dependencies (this may take a few minutes on first run)...
python -m pip install --upgrade pip --quiet
python -m pip install -r python_requirements.txt --quiet
if errorlevel 1 (
    echo ERROR: Dependency installation failed.
    pause
    exit /b 1
)
echo [OK] Dependencies installed
echo.

REM Warn if ffmpeg is missing
where ffmpeg >nul 2>&1
if errorlevel 1 (
    echo WARNING: ffmpeg not found on PATH.
    echo   WAV-to-MP3 conversion will not work until ffmpeg is installed.
    echo   Download from: https://ffmpeg.org/download.html
    echo   Then add the ffmpeg\bin folder to your PATH environment variable.
    echo.
)

REM Launch the app
echo Launching OHM...
echo.
python app.py

REM Keep window open if the app exits with an error
if errorlevel 1 (
    echo.
    echo OHM exited with an error. See messages above.
    pause
)

endlocal
