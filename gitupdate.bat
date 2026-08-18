@echo off
title Gamekaren - GitHub Sync
cd /d C:\gamekaren_project

echo ==========================================
echo        GAMEKAREN GITHUB SYNC
echo ==========================================
echo.

echo [1/5] Checking GitHub connection...
git fetch origin

if errorlevel 1 (
    echo.
    echo ERROR: Could not connect to GitHub.
    echo.
    pause
    exit /b 1
)

echo.
echo [2/5] Checking local changes...

git status --porcelain

if "%errorlevel%"=="0" (
    git status --porcelain > "%temp%\gamekaren_git_status.txt"
)

for /f %%A in ('type "%temp%\gamekaren_git_status.txt" 2^>nul') do goto LOCAL_CHANGES

echo.
echo No local changes found.
goto PULL

:LOCAL_CHANGES

echo.
echo Local changes detected.
echo.

echo [3/5] Saving local changes to GitHub...

git add .

git commit -m "Update Gamekaren system"

if errorlevel 1 (
    echo.
    echo ERROR: Commit failed.
    echo.
    pause
    exit /b 1
)

git push origin main

if errorlevel 1 (
    echo.
    echo ERROR: Push to GitHub failed.
    echo.
    pause
    exit /b 1
)

echo.
echo Local changes successfully uploaded to GitHub.
echo.

:PULL

echo [4/5] Getting latest changes from GitHub...

git pull origin main

if errorlevel 1 (
    echo.
    echo ERROR: GitHub update failed.
    echo.
    echo Please check for conflicts.
    echo.
    pause
    exit /b 1
)

echo.
echo [5/5] Synchronization completed.
echo.

del "%temp%\gamekaren_git_status.txt" >nul 2>&1

echo ==========================================
echo       GITHUB SYNC COMPLETED SUCCESSFULLY
echo ==========================================
echo.

pause