@echo off
chcp 65001 >nul
REM Windows Monocular Mode Quick Start Script

echo ==========================================
echo Real-time Visual Obstacle Avoidance System
echo Windows Monocular Mode
echo ==========================================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found, please install Python 3.11+
    pause
    exit /b 1
)

REM Check virtual environment
if exist venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo Warning: Virtual environment not found, using system Python
)

REM Check dependencies
echo Checking dependencies...
python -c "import cv2, numpy, yaml, pygame" >nul 2>&1
if errorlevel 1 (
    echo Warning: Missing dependencies, installing...
    pip install -r requirements.txt
)

echo.
echo Starting system...
echo Press ESC to exit
echo.
echo Display modes:
echo   - Default (BEV): python src/main_mono.py --camera 0
echo   - OpenCV: python src/main_mono.py --camera 0 --display opencv
echo   - Both: python src/main_mono.py --camera 0 --display both
echo.

REM Run monocular mode (default BEV display)
python src/main_mono.py --config configs/system_config_mono.yaml --camera 0

pause

