# Registers Job Hunter Bot to run in the background at Windows login.
# Run from an elevated PowerShell if Task Scheduler access is restricted.

param(
    [string]$ExePath = (Join-Path $PSScriptRoot "..\dist\JobHunterBot.exe"),
    [string]$TaskName = "JobHunterBot"
)

$ExePath = (Resolve-Path $ExePath -ErrorAction Stop).Path
$WorkDir = Split-Path $ExePath -Parent

$action = New-ScheduledTaskAction -Execute $ExePath -Argument "watch" -WorkingDirectory $WorkDir
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Force

Write-Host "Scheduled task '$TaskName' created."
Write-Host "Job Hunter Bot will start in the background when you log in."
Write-Host "Logs: $WorkDir\data\job-hunter.log"
