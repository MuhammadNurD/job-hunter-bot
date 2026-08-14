param(
    [string]$ExePath = (Join-Path $PSScriptRoot "..\dist\JobHunterBot.exe")
)

$ExePath = (Resolve-Path $ExePath -ErrorAction Stop).Path
$WorkDir = Split-Path $ExePath -Parent
$shell = New-Object -ComObject WScript.Shell

$desktop = [Environment]::GetFolderPath("Desktop")
$startMenu = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs"

foreach ($folder in @($desktop, $startMenu, $WorkDir)) {
    $shortcutPath = Join-Path $folder "Job Hunter Bot.lnk"
    $shortcut = $shell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = $ExePath
    $shortcut.WorkingDirectory = $WorkDir
    $shortcut.Description = "Start Job Hunter Bot in the system tray"
    $shortcut.Save()
}

Write-Host "Shortcuts created on the Desktop, Start Menu, and dist folder."
Write-Host "Double-click 'Job Hunter Bot' to start it."
