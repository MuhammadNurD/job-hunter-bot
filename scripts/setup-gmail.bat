@echo off
setlocal

echo Gmail setup for Job Hunter Bot
echo ==============================
echo Account: dalwai.mn@gmail.com
echo.
echo Before continuing, create a Gmail App Password:
echo   1. Open https://myaccount.google.com/apppasswords
echo   2. Sign in as dalwai.mn@gmail.com
echo   3. Turn on 2-Step Verification if prompted
echo   4. Create an app password named "Job Hunter Bot"
echo   5. Copy the 16-character password (looks like: abcd efgh ijkl mnop)
echo.

set /p APP_PASSWORD="Paste your Gmail App Password here: "
if "%APP_PASSWORD%"=="" (
    echo No password entered. Exiting.
    exit /b 1
)

setx JOB_HUNTER_SMTP_PASSWORD "%APP_PASSWORD%"
if errorlevel 1 (
    echo Failed to save environment variable.
    exit /b 1
)

echo.
echo Saved JOB_HUNTER_SMTP_PASSWORD for future logins.
echo.
echo Next steps:
echo   1. Edit profile.json with your LinkedIn details
echo   2. Run: dist\JobHunterBot.exe test-email
echo   3. Run: dist\JobHunterBot.exe watch
echo      or use scripts\install-windows-task.ps1 for auto-start
echo.
echo Note: Close and reopen Command Prompt so the new env var is loaded.
echo.

endlocal
