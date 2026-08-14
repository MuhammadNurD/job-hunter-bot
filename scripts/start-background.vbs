' Starts Job Hunter Bot without a visible console window.
' Double-click this file after configuring dist\config.yaml and dist\profile.json.

Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
appDir = fso.GetParentFolderName(scriptDir)
exePath = appDir & "\dist\JobHunterBot.exe"

If Not fso.FileExists(exePath) Then
    MsgBox "JobHunterBot.exe not found. Run build.bat first.", vbCritical, "Job Hunter Bot"
    WScript.Quit 1
End If

shell.CurrentDirectory = appDir & "\dist"
shell.Run """" & exePath & """ watch", 0, False
