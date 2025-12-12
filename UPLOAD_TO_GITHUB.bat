@echo off
chcp 65001 >nul
echo ========================================
echo GitHub Upload Helper Script
echo ========================================
echo.

REM Check if Git is installed
git --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Git is not installed or not in PATH
    echo Please install Git from: https://git-scm.com/download/win
    echo After installation, restart this script
    pause
    exit /b 1
)

echo [OK] Git is installed
echo.

REM Check if already a git repository
if exist .git (
    echo [INFO] Git repository already initialized
    git status
) else (
    echo [INFO] Initializing Git repository...
    git init
    echo [OK] Git repository initialized
    echo.
    
    echo [INFO] Adding all files...
    git add .
    echo [OK] Files added
    echo.
    
    echo [INFO] Creating initial commit...
    git commit -m "Initial commit: Real-time Visual Obstacle Avoidance System"
    echo [OK] Initial commit created
    echo.
)

echo ========================================
echo Next Steps:
echo ========================================
echo.
echo 1. Create a new repository on GitHub:
echo    - Go to https://github.com/new
echo    - Repository name: YCTarget (or your preferred name)
echo    - Choose Public or Private
echo    - DO NOT initialize with README
echo    - Click "Create repository"
echo.
echo 2. Connect local repository to GitHub:
echo    git remote add origin https://github.com/YOUR_USERNAME/YCTarget.git
echo.
echo 3. Push code to GitHub:
echo    git branch -M main
echo    git push -u origin main
echo.
echo For detailed instructions, see: docs/GITHUB_UPLOAD.md
echo.
echo ========================================
pause

