@echo off
setlocal

echo Publish Job Hunter Bot to GitHub
echo ================================
echo.

gh auth status >nul 2>&1
if errorlevel 1 (
    echo GitHub CLI is not logged in.
    echo Run: gh auth login
    echo Then run this script again.
    exit /b 1
)

set /p REPO_NAME="GitHub repo name [job-hunter-bot]: "
if "%REPO_NAME%"=="" set REPO_NAME=job-hunter-bot

set /p VISIBILITY="Visibility public/private [private]: "
if "%VISIBILITY%"=="" set VISIBILITY=private

cd /d "%~dp0.."

git branch -M main
gh repo create %REPO_NAME% --source=. --remote=origin --push --%VISIBILITY%

if errorlevel 1 (
    echo.
    echo If the repo already exists, try:
    echo   git remote add origin https://github.com/YOUR_USERNAME/%REPO_NAME%.git
    echo   git push -u origin main
    exit /b 1
)

echo.
echo Done! Open in Cursor:
echo   1. Cursor - File - Clone from GitHub
echo   2. Select %REPO_NAME%
echo.
for /f "delimiters=" %%i in ('gh repo view --json url -q .url') do echo Repo URL: %%i

endlocal
