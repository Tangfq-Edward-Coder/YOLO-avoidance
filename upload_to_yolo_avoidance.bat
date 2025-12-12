@echo off
chcp 65001 >nul
echo ========================================
echo Uploading to GitHub Repository
echo Repository: YOLO-avoidance
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

REM Set repository URL
set REPO_URL=https://github.com/Tangfq-Edward-Coder/YOLO-avoidance.git

REM Initialize Git repository if not exists
if not exist .git (
    echo [INFO] Initializing Git repository...
    git init
    echo [OK] Git repository initialized
    echo.
)

REM Check remote
git remote get-url origin >nul 2>&1
if errorlevel 1 (
    echo [INFO] Adding remote repository...
    git remote add origin %REPO_URL%
    echo [OK] Remote repository added: %REPO_URL%
) else (
    echo [INFO] Updating remote repository URL...
    git remote set-url origin %REPO_URL%
    echo [OK] Remote repository updated: %REPO_URL%
)
echo.

REM Add all files
echo [INFO] Adding all files...
git add .
echo [OK] Files added
echo.

REM Check if there are changes to commit
git diff --cached --quiet
if errorlevel 1 (
    echo [INFO] Creating commit...
    git commit -m "Initial commit: Real-time Visual Obstacle Avoidance System"
    echo [OK] Commit created
) else (
    echo [INFO] No changes to commit
)
echo.

REM Set branch to main
echo [INFO] Setting branch to main...
git branch -M main
echo [OK] Branch set to main
echo.

echo ========================================
echo Ready to push to GitHub
echo ========================================
echo.
echo Repository: %REPO_URL%
echo.
echo [INFO] Pushing to GitHub...
echo Note: You may be prompted for GitHub credentials
echo       Use your GitHub username and Personal Access Token
echo.
git push -u origin main

if errorlevel 1 (
    echo.
    echo [ERROR] Push failed. Common reasons:
    echo 1. Authentication failed - Use Personal Access Token instead of password
    echo 2. Repository doesn't exist or you don't have access
    echo 3. Network connection issues
    echo.
    echo For help, see: docs/GITHUB_UPLOAD.md
) else (
    echo.
    echo [SUCCESS] Code uploaded successfully!
    echo View your repository at: %REPO_URL%
)

echo.
pause

