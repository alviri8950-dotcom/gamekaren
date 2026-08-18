@echo off
setlocal EnableExtensions EnableDelayedExpansion

title Gamekaren - Safe GitHub Update

cd /d C:\gamekaren_project

echo ==========================================
echo       GAMEKAREN SAFE GITHUB UPDATE
echo ==========================================
echo.

REM ==========================================
REM SETTINGS
REM ==========================================

set "PROJECT=C:\gamekaren_project"
set "DB=%PROJECT%\db.sqlite3"
set "BACKUP_DIR=%PROJECT%\backups"
set "BRANCH=main"

REM ==========================================
REM 1 - CHECK DATABASE
REM ==========================================

echo [1/7] Checking database...

if not exist "%DB%" (
    echo.
    echo ERROR: Database not found:
    echo %DB%
    echo.
    echo Update cancelled.
    pause
    exit /b 1
)

echo Database found.
echo.

REM ==========================================
REM 2 - CREATE DATABASE BACKUP
REM ==========================================

echo [2/7] Creating database backup...

if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

for /f "tokens=1-3 delims=/" %%a in ("%date%") do (
    set "DATE=%%c-%%b-%%a"
)

for /f "tokens=1-2 delims=:" %%a in ("%time%") do (
    set "HOUR=%%a"
    set "MINUTE=%%b"
)

set "HOUR=!HOUR: =0!"

set "BACKUP_FILE=%BACKUP_DIR%\db_!DATE!_!HOUR!-!MINUTE!.sqlite3"

copy /Y "%DB%" "!BACKUP_FILE!" >nul

if errorlevel 1 (
    echo.
    echo ERROR: Database backup failed.
    echo.
    echo UPDATE CANCELLED.
    echo No changes were made.
    echo.
    pause
    exit /b 1
)

echo Backup created:
echo !BACKUP_FILE!
echo.

REM ==========================================
REM 3 - CHECK GIT
REM ==========================================

echo [3/7] Checking GitHub connection...

git fetch origin

if errorlevel 1 (
    echo.
    echo ERROR: Could not connect to GitHub.
    echo.
    echo Database backup is safe.
    echo Update cancelled.
    echo.
    pause
    exit /b 1
)

echo GitHub connection successful.
echo.

REM ==========================================
REM 4 - CHECK LOCAL CODE CHANGES
REM ==========================================

echo [4/7] Checking local project changes...

git status --short

git status --porcelain > "%TEMP%\gamekaren_status.txt"

for %%A in ("%TEMP%\gamekaren_status.txt") do set "STATUS_SIZE=%%~zA"

if not "!STATUS_SIZE!"=="0" (
    echo.
    echo ==========================================
    echo WARNING: LOCAL CODE CHANGES DETECTED
    echo ==========================================
    echo.
    echo The local project contains changes that
    echo are not committed to Git.
    echo.
    echo GitHub is the source of the application code.
    echo To prevent overwriting local work,
    echo the update has been cancelled.
    echo.
    echo Database backup is safe.
    echo No files were deleted.
    echo No files were overwritten.
    echo.
    del "%TEMP%\gamekaren_status.txt" >nul 2>&1
    pause
    exit /b 2
)

del "%TEMP%\gamekaren_status.txt" >nul 2>&1

REM ==========================================
REM 5 - CHECK FOR NEW GITHUB COMMITS
REM ==========================================

echo [5/7] Checking GitHub for updates...

for /f %%A in ('git rev-parse HEAD') do set "LOCAL_COMMIT=%%A"

for /f %%A in ('git rev-parse origin/%BRANCH%') do set "REMOTE_COMMIT=%%A"

echo Local : !LOCAL_COMMIT!
echo GitHub: !REMOTE_COMMIT!
echo.

if "!LOCAL_COMMIT!"=="!REMOTE_COMMIT!" (
    echo Already up to date.
    goto FINISH
)

echo New GitHub changes detected.
echo.

REM ==========================================
REM 6 - CHECK MIGRATIONS
REM ==========================================

echo [6/7] Checking for database migrations...

git diff --name-only !LOCAL_COMMIT! origin/%BRANCH% -- "*.py" > "%TEMP%\gamekaren_python_changes.txt"

set "MIGRATION_FOUND=0"

for /f "delims=" %%A in ("%TEMP%\gamekaren_python_changes.txt") do (
    echo %%A | findstr /I /C:"migrations\" >nul
    if not errorlevel 1 (
        set "MIGRATION_FOUND=1"
    )
)

del "%TEMP%\gamekaren_python_changes.txt" >nul 2>&1

if "!MIGRATION_FOUND!"=="1" (
    echo.
    echo ==========================================
    echo       DATABASE CHANGES DETECTED
    echo ==========================================
    echo.
    echo The new GitHub version contains migration
    echo changes.
    echo.
    echo AUTOMATIC MIGRATION WILL NOT BE EXECUTED.
    echo.
    echo Your database contains real business data:
    echo - Products
    echo - Users
    echo - Groups
    echo - Invoices
    echo - Inventory
    echo - Other data
    echo.
    echo Update cancelled for safety.
    echo.
    echo Database backup is available at:
    echo %BACKUP_DIR%
    echo.
    pause
    exit /b 3
)

REM ==========================================
REM 7 - UPDATE CODE ONLY
REM ==========================================

echo No migration files detected.
echo.
echo Updating application code from GitHub...
echo.

git merge --ff-only origin/%BRANCH%

if errorlevel 1 (
    echo.
    echo ==========================================
    echo             UPDATE FAILED
    echo ==========================================
    echo.
    echo Git could not safely update the project.
    echo.
    echo NO forced update was performed.
    echo NO local files were deleted.
    echo.
    echo Database backup is safe.
    echo.
    pause
    exit /b 4
)

:FINISH

echo.
echo ==========================================
echo       UPDATE COMPLETED SUCCESSFULLY
echo ==========================================
echo.
echo Application code : Synchronized
echo Database         : Preserved
echo Migration        : NOT EXECUTED
echo Backup           : Created
echo.
echo ==========================================
echo.

pause
exit /b 0