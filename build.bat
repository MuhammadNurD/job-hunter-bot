@echo off
setlocal

echo Building Job Hunter Bot Windows executable...
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not on PATH.
    echo Install Python 3.11+ from https://www.python.org/downloads/
    exit /b 1
)

python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller

pyinstaller --clean job_hunter_bot.spec

if errorlevel 1 (
    echo Build failed.
    exit /b 1
)

copy /Y config.example.yaml dist\config.example.yaml >nul
copy /Y profile.example.json dist\profile.example.json >nul

if not exist dist\config.yaml copy /Y config.example.yaml dist\config.yaml
if not exist dist\profile.json copy /Y profile.example.json dist\profile.json
if not exist dist\data mkdir dist\data

echo.
echo Build complete: dist\JobHunterBot.exe
echo Double-click dist\JobHunterBot.exe to start it in the system tray.
echo.

powershell -ExecutionPolicy Bypass -File "%~dp0scripts\install-shortcuts.ps1"

echo Next steps:
echo   1. Edit dist\config.yaml  - enable email alerts
echo   2. Edit dist\profile.json   - add your LinkedIn profile
echo   3. Double-click dist\JobHunterBot.exe or the Desktop shortcut
echo   4. Optional: powershell -ExecutionPolicy Bypass -File scripts\install-windows-task.ps1
echo.

endlocal
